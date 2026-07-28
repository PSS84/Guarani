# -*- coding: utf-8 -*-
"""
Dados para o dashboard "Análise de Situação" (guarani/templates/analise_situacao.html).

Consulta o Jira Cloud (via jira_conexao) para uma organização (empresa/cliente) e
monta o payload consumido pela página: KPIs, distribuição por status, tempo em
aberto, tickets detalhados, ações prioritárias e observações estratégicas.

"Saúde do cliente", "ações prioritárias" e "observações estratégicas" são
calculadas por regras objetivas sobre os dados do Jira (dias em aberto, dias
desde a última interação, status comercial) — não há texto interpretativo
gerado sobre o cliente.
"""

import time
from collections import Counter
from datetime import datetime, timezone
from statistics import mean

from jira_conexao import conectar, api_get

_CACHE_TTL_ORGS = 600      # 10 min
_CACHE_TTL_DADOS = 120     # 2 min

_cache_orgs = {"ts": 0, "dados": None}
_cache_dados = {}  # org_id -> {"ts": ..., "dados": ...}
_jira_client = {"cliente": None, "ts": 0}

_CAMPO_MODULO = "customfield_10613"

_TICKET_FIELDS = f"summary,status,issuetype,assignee,reporter,created,project,{_CAMPO_MODULO}"
_FIELDS_ENCERRADOS = "summary,status,issuetype,assignee,reporter,created,resolutiondate,resolution"

# Classificação do campo "Resolução" para desfechos comerciais (propostas/orçamentos).
# Mapeado a partir das opções cadastradas no Jira (tela "Concluir" do chamado).
#
# Por ora só classificamos "recusado" (o cliente não aprovou). O indicador de
# "aprovado" foi removido: checamos que "[Comercial] - Serviço contratado realizado"
# é usada em apenas 6 de 1.721 tickets que passaram por "Proposta Comercial" e têm
# resolução — a grande maioria das aprovações fecha com resoluções genéricas
# ("Realizado com/sem interação cliente"), indistinguíveis de qualquer chamado comum
# de suporte sem cruzar com o histórico de status. Fica pendente de nova regra.


def _norm_resolucao(s: str) -> str:
    return (s or "").strip().replace("–", "-").replace("—", "-")


_RESOLUCOES_COMERCIAL_RECUSADA = {
    _norm_resolucao(r) for r in [
        "[Comercial] - Só fez uma sugestão de melhoria",
        "[Comercial] - Não concorda com pagto, func básica",
        "[Comercial] - Sem aprovação financeira (budget)",
        "[Comercial] - Já encontrou uma alternativa",
        "[Comercial] - Não concorda com pagto, melhora sistema",
        "[Comercial] - Não concorda com pagto, atende outros clientes",
        "[Comercial] - Não aprovado, aguarda entrega tickets já pagos",
        "Orçamento não Aprovado",
        "Sem Retorno de Orçamento",
    ]
}


def _classificar_comercial(resolucao_nome: str):
    """Classifica uma resolução do Jira como 'recusado' ou None (não comercial / aprovado ainda não modelado)."""
    r = _norm_resolucao(resolucao_nome)
    if not r:
        return None
    if r in _RESOLUCOES_COMERCIAL_RECUSADA:
        return "recusado"
    return None


def _get_jira(timeout: int = 30):
    agora = time.time()
    if _jira_client["cliente"] is None or agora - _jira_client["ts"] > 300:
        _jira_client["cliente"] = conectar(timeout=timeout)
        _jira_client["ts"] = agora
    return _jira_client["cliente"]


def _adf_to_text(node) -> str:
    """Achata um documento ADF (corpo de comentário do Jira) para texto simples."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    partes = [_adf_to_text(c) for c in node.get("content", []) or []]
    junta = "\n" if node.get("type") in ("paragraph", "heading", "blockquote") else ""
    return junta.join(partes) if junta else "".join(partes)


def listar_organizacoes(forcar: bool = False):
    """Lista organizações (empresas/clientes) cadastradas no Jira Service Management."""
    agora = time.time()
    if not forcar and _cache_orgs["dados"] is not None and agora - _cache_orgs["ts"] < _CACHE_TTL_ORGS:
        return _cache_orgs["dados"]

    jira = _get_jira()
    orgs = []
    start = 0
    while True:
        data = api_get(jira, "/rest/servicedeskapi/organization", {"start": start, "limit": 50})
        valores = data.get("values", [])
        orgs.extend({"id": o["id"], "nome": o["name"]} for o in valores)
        if data.get("isLastPage", True) or not valores:
            break
        start += 50

    orgs.sort(key=lambda o: o["nome"].lower())
    _cache_orgs["dados"] = orgs
    _cache_orgs["ts"] = agora
    return orgs


def _eh_comercial(status_nome: str) -> bool:
    return "comercial" in status_nome.lower()


def _eh_execucao_desenvolvimento(status_nome: str) -> bool:
    s = status_nome.lower()
    return "execu" in s or "desenvolv" in s


def _buscar_issues(jira, jql: str, fields: str):
    """Busca todas as issues de uma JQL, paginando via nextPageToken."""
    issues = []
    next_token = None
    while True:
        params = {"jql": jql, "maxResults": 100, "fields": fields}
        if next_token:
            params["nextPageToken"] = next_token
        data = api_get(jira, "/rest/api/3/search/jql", params)
        lote = data.get("issues", [])
        issues.extend(lote)
        next_token = data.get("nextPageToken")
        if data.get("isLast", True) or not next_token:
            break
    return issues


def _valor_modulo(fields: dict) -> str:
    campo = fields.get(_CAMPO_MODULO)
    return campo.get("value") if isinstance(campo, dict) and campo.get("value") else "Sem módulo"


# "Equipe comercial" para fins de destacar quais chamados encerrados foram atribuídos
# a Paulo ou Rayssa. Usa o campo "responsável" (assignee) — o autor da transição de
# status no changelog costuma ser só "Guarani Admin" (automação/SLA), não reflete
# quem realmente trabalhou o chamado.
_EQUIPE_COMERCIAL_TERMOS = ("paulo", "rayssa")


def _eh_equipe_comercial(nome: str) -> bool:
    n = (nome or "").lower()
    return any(t in n for t in _EQUIPE_COMERCIAL_TERMOS)


def _montar_encerrados(jira, org_id, org_nome: str, dias: int = 30):
    """Chamados encerrados (statusCategory = Done) nos últimos N dias."""
    jql = f"Organizations = {org_id} AND statusCategory = Done AND resolved >= -{dias}d ORDER BY resolutiondate DESC"
    issues = _buscar_issues(jira, jql, _FIELDS_ENCERRADOS)

    encerrados = []
    for it in issues:
        f = it["fields"]
        chave = it["key"]
        status_final = f["status"]["name"]

        criado = datetime.strptime(f["created"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        resolvido_str = f.get("resolutiondate")
        if resolvido_str:
            resolvido = datetime.strptime(resolvido_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            dias_total = (resolvido - criado).days
        else:
            dias_total = None

        reporter = f.get("reporter") or {}
        assignee = f.get("assignee") or {}
        resolucao = (f.get("resolution") or {}).get("name", "")
        responsavel = assignee.get("displayName", "Sem responsável")

        encerrados.append({
            "chave": chave,
            "url": f"{jira.base_url}/browse/{chave}",
            "organizacao": org_nome,
            "cliente": reporter.get("displayName", "(sem contato)"),
            "tipo": f["issuetype"]["name"],
            "status": status_final,
            "resolucao": resolucao or "—",
            "classificacao_comercial": _classificar_comercial(resolucao),
            "responsavel": responsavel,
            "fechamento_equipe_comercial": _eh_equipe_comercial(responsavel),
            "resumo": (f.get("summary") or "").strip(),
            "criado_em": f["created"][:10],
            "encerrado_em": resolvido_str[:10] if resolvido_str else "",
            "dias_total": dias_total,
        })
    return encerrados


def _montar_indicador_comercial(jira, org_id, ano: int):
    """Propostas comerciais RECUSADAS no ano corrente, por motivo e por responsável.

    O indicador de "aprovado" foi removido por enquanto (ver comentário acima de
    _classificar_comercial) — só o lado "recusado" é confiável hoje.
    """
    jql = (
        f'Organizations = {org_id} AND statusCategory = Done AND resolution is not EMPTY '
        f'AND resolved >= "{ano}-01-01" ORDER BY resolutiondate DESC'
    )
    issues = _buscar_issues(jira, jql, "resolution,resolutiondate,assignee")

    recusadas = 0
    por_motivo = {}       # motivo -> {"total": n, "tickets": [{"chave", "url"}, ...]}
    por_responsavel = {}  # nome -> {"total": n, "tickets": [...]}
    for it in issues:
        resolucao = (it["fields"].get("resolution") or {}).get("name", "")
        if _classificar_comercial(resolucao) != "recusado":
            continue

        chave = it["key"]
        ticket_ref = {"chave": chave, "url": f"{jira.base_url}/browse/{chave}"}
        recusadas += 1

        m_info = por_motivo.setdefault(resolucao, {"total": 0, "tickets": []})
        m_info["total"] += 1
        m_info["tickets"].append(ticket_ref)

        assignee = it["fields"].get("assignee") or {}
        nome = assignee.get("displayName", "Sem responsável")
        r_info = por_responsavel.setdefault(nome, {"total": 0, "tickets": []})
        r_info["total"] += 1
        r_info["tickets"].append(ticket_ref)

    por_motivo_lista = sorted(
        [{"motivo": m, "total": v["total"], "tickets": v["tickets"]} for m, v in por_motivo.items()],
        key=lambda x: x["total"], reverse=True,
    )
    responsaveis = sorted(
        [
            {"nome": n, "total": v["total"], "tickets": v["tickets"], "equipe_comercial": _eh_equipe_comercial(n)}
            for n, v in por_responsavel.items()
        ],
        key=lambda x: x["total"], reverse=True,
    )

    return {
        "ano": ano,
        "total_recusadas": recusadas,
        "por_motivo": por_motivo_lista,
        "por_responsavel": responsaveis,
    }


def _montar_volume_anual(jira, org_id, ano: int):
    """Total de chamados abertos (criados) pelo cliente no ano corrente, e quantos já foram encerrados."""
    jql = f'Organizations = {org_id} AND created >= "{ano}-01-01" AND created < "{ano + 1}-01-01"'
    issues = _buscar_issues(jira, jql, "status")

    total = len(issues)
    encerrados = sum(1 for it in issues if it["fields"]["status"]["statusCategory"]["key"] == "done")

    return {
        "ano": ano,
        "total_abertos": total,
        "encerrados": encerrados,
        "em_aberto": total - encerrados,
    }


def _montar_ranking_modulo(jira, org_id, ano: int):
    """Ranking de chamados abertos (criados) no ano corrente por Módulo."""
    jql = f'Organizations = {org_id} AND created >= "{ano}-01-01" AND created < "{ano + 1}-01-01"'
    issues = _buscar_issues(jira, jql, _CAMPO_MODULO)

    contagem = Counter(_valor_modulo(it["fields"]) for it in issues)

    return {
        "ano": ano,
        "total": sum(contagem.values()),
        "ranking": [{"modulo": m, "total": c} for m, c in contagem.most_common()],
    }


def montar_dashboard(org_id: str, forcar: bool = False) -> dict:
    """Consulta o Jira e monta o payload completo do dashboard para uma organização."""
    agora = time.time()
    cache = _cache_dados.get(org_id)
    if not forcar and cache is not None and agora - cache["ts"] < _CACHE_TTL_DADOS:
        return cache["dados"]

    jira = _get_jira()

    organizacoes = {o["id"]: o["nome"] for o in listar_organizacoes()}
    org_nome = organizacoes.get(str(org_id), f"Organização {org_id}")

    jql = f"Organizations = {org_id} AND statusCategory != Done ORDER BY created ASC"
    issues = _buscar_issues(jira, jql, _TICKET_FIELDS)

    hoje = datetime.now(timezone.utc)
    tickets = []
    for it in issues:
        f = it["fields"]
        chave = it["key"]

        criado = datetime.strptime(f["created"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        dias_aberto = (hoje - criado).days

        reporter = f.get("reporter") or {}
        assignee = f.get("assignee") or {}

        comentarios = api_get(jira, f"/rest/api/3/issue/{chave}/comment", {"orderBy": "-created", "maxResults": 1})
        lista_com = comentarios.get("comments", [])
        if lista_com:
            ultimo = lista_com[0]
            autor = ultimo.get("author", {}).get("displayName", "?")
            criado_com = ultimo["created"]
            data_com = datetime.strptime(criado_com[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            dias_desde_interacao = (hoje - data_com).days
            texto = " ".join(_adf_to_text(ultimo.get("body")).split())
        else:
            autor, criado_com, dias_desde_interacao, texto = "(sem comentários)", "", dias_aberto, ""

        tickets.append({
            "chave": chave,
            "url": f"{jira.base_url}/browse/{chave}",
            "organizacao": org_nome,
            "cliente": reporter.get("displayName", "(sem contato)"),
            "tipo": f["issuetype"]["name"],
            "status": f["status"]["name"],
            "modulo": _valor_modulo(f),
            "responsavel": assignee.get("displayName", "Sem responsável"),
            "resumo": (f.get("summary") or "").strip(),
            "criado_em": f["created"][:10],
            "dias_aberto": dias_aberto,
            "ultima_interacao_autor": autor,
            "ultima_interacao_data": criado_com[:10] if criado_com else "",
            "dias_desde_ultima_interacao": dias_desde_interacao,
            "o_que_foi_dito": texto,
        })

    tickets.sort(key=lambda t: t["dias_aberto"], reverse=True)

    total = len(tickets)
    dias_lista = [t["dias_aberto"] for t in tickets]
    maior_tempo = max(dias_lista) if dias_lista else 0
    media_tempo = round(mean(dias_lista)) if dias_lista else 0

    chamados_comerciais = sum(1 for t in tickets if _eh_comercial(t["status"]))
    em_exec_dev = sum(1 for t in tickets if _eh_execucao_desenvolvimento(t["status"]))
    alto_risco = sum(1 for t in tickets if t["dias_desde_ultima_interacao"] >= 30)

    # --- saúde do cliente (0-100), por regras objetivas ---
    pontos = 100
    for t in tickets:
        if t["dias_aberto"] > 180:
            pontos -= 15
        elif t["dias_aberto"] > 90:
            pontos -= 10
        elif t["dias_aberto"] > 60:
            pontos -= 5
        if t["dias_desde_ultima_interacao"] >= 30:
            pontos -= 10
        elif t["dias_desde_ultima_interacao"] >= 15:
            pontos -= 5
        if _eh_comercial(t["status"]):
            pontos -= 5
    pontos = max(0, min(100, pontos))
    if pontos >= 80:
        saude_label, saude_cor = "SAUDÁVEL", "verde"
    elif pontos >= 50:
        saude_label, saude_cor = "ATENÇÃO", "amarelo"
    else:
        saude_label, saude_cor = "CRÍTICO", "vermelho"

    contagem_status = Counter(t["status"] for t in tickets)
    distribuicao_status = [{"status": s, "total": c} for s, c in contagem_status.most_common()]

    tempo_aberto = [{"chave": t["chave"], "dias": t["dias_aberto"]} for t in tickets]

    contagem_resp = Counter(t["responsavel"] for t in tickets)
    por_responsavel = [{"nome": n, "total": c} for n, c in contagem_resp.most_common()]

    # --- ações prioritárias (regras objetivas) ---
    acoes = []
    for t in tickets:
        if t["dias_aberto"] > 180:
            acoes.append({
                "nivel": "CRITICO",
                "descricao": f"{t['chave']} parado há {t['dias_aberto']} dias — validar necessidade ou encerrar",
                "responsavel": t["responsavel"], "prazo": "HOJE",
            })
        elif _eh_comercial(t["status"]):
            acoes.append({
                "nivel": "ALTO",
                "descricao": f"{t['chave']} aguardando aprovação/fechamento comercial",
                "responsavel": t["responsavel"], "prazo": "24h",
            })
        elif t["dias_desde_ultima_interacao"] >= 15:
            acoes.append({
                "nivel": "MEDIA",
                "descricao": f"{t['chave']} sem interação há {t['dias_desde_ultima_interacao']} dias — cobrar retorno",
                "responsavel": t["responsavel"], "prazo": "48h",
            })
    ordem_nivel = {"CRITICO": 0, "ALTO": 1, "MEDIA": 2}
    acoes.sort(key=lambda a: ordem_nivel[a["nivel"]])
    acoes = acoes[:6]

    com_interacao = [t for t in tickets if t["ultima_interacao_data"]]
    ultimas_interacoes = sorted(com_interacao, key=lambda t: t["ultima_interacao_data"], reverse=True)[:5]

    # --- observações estratégicas (regras objetivas, sem juízo de valor) ---
    observacoes = []
    if chamados_comerciais:
        observacoes.append(f"Cliente possui {chamados_comerciais} chamado(s) comercial(is) pendente(s) de aprovação/cobrança.")
    antigos = [t for t in tickets if t["dias_aberto"] > 180]
    if antigos:
        chaves = ", ".join(t["chave"] for t in antigos[:3])
        observacoes.append(f"{len(antigos)} chamado(s) aberto(s) há mais de 180 dias sem conclusão ({chaves}).")
    if por_responsavel:
        top = por_responsavel[0]
        if total >= 3 and top["total"] / total >= 0.4:
            observacoes.append(f"{top['total']} de {total} chamados concentrados em {top['nome']}.")
    if alto_risco:
        observacoes.append(f"{alto_risco} chamado(s) sem interação há 30 dias ou mais — risco de estagnação.")
    if total >= 5:
        observacoes.append(f"Cliente possui {total} demandas simultâneas em aberto.")

    intervencoes = []
    if antigos:
        intervencoes.append("Resolver chamados antigos parados")
    if em_exec_dev:
        intervencoes.append("Acompanhar chamados em execução/desenvolvimento")
    if chamados_comerciais:
        intervencoes.append("Fechar propostas comerciais pendentes")
    if alto_risco:
        intervencoes.append("Cobrar retorno e alinhar com o cliente")

    chamados_encerrados_30d = _montar_encerrados(jira, org_id, org_nome, dias=30)
    indicador_comercial = _montar_indicador_comercial(jira, org_id, hoje.year)
    volume_anual = _montar_volume_anual(jira, org_id, hoje.year)
    ranking_modulo = _montar_ranking_modulo(jira, org_id, hoje.year)

    fechados_comercial = sum(1 for t in chamados_encerrados_30d if t["fechamento_equipe_comercial"])
    resumo_encerrados = {
        "total": len(chamados_encerrados_30d),
        "pela_equipe_comercial": fechados_comercial,
    }

    dados = {
        "organizacao": {"id": str(org_id), "nome": org_nome},
        "responsavel_comercial": jira.usuario,
        "data_referencia": hoje.strftime("%d/%m/%Y"),
        "kpis": {
            "total_chamados": total,
            "maior_tempo_aberto_dias": maior_tempo,
            "media_tempo_aberto_dias": media_tempo,
            "chamados_comerciais": chamados_comerciais,
            "em_execucao_desenvolvimento": em_exec_dev,
            "alto_risco_sem_evolucao": alto_risco,
        },
        "saude_cliente": {"percentual": pontos, "label": saude_label, "cor": saude_cor},
        "distribuicao_status": distribuicao_status,
        "tempo_aberto": tempo_aberto,
        "chamados_por_responsavel": por_responsavel,
        "tickets": tickets,
        "chamados_encerrados_30d": chamados_encerrados_30d,
        "resumo_encerrados": resumo_encerrados,
        "indicador_comercial": indicador_comercial,
        "volume_anual": volume_anual,
        "ranking_modulo": ranking_modulo,
        "acoes_prioritarias": acoes,
        "ultimas_interacoes": ultimas_interacoes,
        "observacoes_estrategicas": observacoes,
        "resumo_executivo": {
            "chamados_totais": total,
            "maior_tempo_aberto_dias": maior_tempo,
            "tempo_medio_aberto_dias": media_tempo,
            "saude_percentual": pontos,
            "saude_label": saude_label,
            "intervencoes": intervencoes,
        },
    }

    _cache_dados[org_id] = {"ts": agora, "dados": dados}
    return dados
