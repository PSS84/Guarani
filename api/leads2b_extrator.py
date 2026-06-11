"""
Extrator da API Leads2b → CSV.

Uso:
    python leads2b_extrator.py                              # extrai oportunidades (padrão, incremental se arquivo existir)
    python leads2b_extrator.py --completo                   # força extração completa desde 2024-11-01
    python leads2b_extrator.py --entidade leads             # extrai leads
    python leads2b_extrator.py --entidade oportunidades     # extrai oportunidades
    python leads2b_extrator.py --entidade prospects         # extrai prospects
    python leads2b_extrator.py --descobrir                  # JSON bruto de 1 registro recente
    python leads2b_extrator.py --desde 2025-01-01           # a partir dessa data
    python leads2b_extrator.py --ate   2025-12-31           # até essa data
    python leads2b_extrator.py --saida meu_arquivo.csv

Variável de ambiente opcional:
    LEADS2B_TOKEN   substitui o token padrão no código
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
TOKEN_V1 = (
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
    ".eyJuYmYiOjE3MzAyMzI2OTQsImlhdCI6MTczMDIzMjY5NCwiY2giOiJZREdmMmRkc091cGdUWmJXN3"
    "BTa255ZG1QWTc1NTVXZSIsInVoIjpudWxsfQ"
    ".ypHHFNPde1zJNiSxTh8_vB-B_Q_0ycqyGCasV17SDOs"
)

BASE_URL  = "https://app.leads2b.com/api/v1"
LIMITE    = 100
PAUSA     = 0.35   # respeita rate limit 200 req/min

# Diretório de saída padrão
_dados_env = os.environ.get("GUARANI_DADOS_DIR")
DIR_SAIDA  = Path(_dados_env) if _dados_env else Path(__file__).resolve().parent.parent / "dados" / "api_leads2b"

# Colunas finais na mesma ordem do CSV exportado pela plataforma
COLUNAS = [
    "Responsável", "ID Oportunidade", "ID Cliente", "ID Contato", "Descrição",
    "Razão social", "Título do negócio", "CNPJ", "Nome do Cliente", "Nome do Contato",
    "Telefone do Contato", "Celular do Contato", "E-mail do contato", "Grupo do cliente",
    "Contatos", "Endereço", "Cidade", "Estado", "Origem", "Origem do cliente",
    "Categoria do cliente", "TAGS", "Funil de vendas", "Etapa do funil de vendas",
    "Forma de Pagamento", "Data esperada de fechamento", "Valor Total", "Valor mensal",
    "Tempo como oportunidade", "Criado por", "Data de Criação", "Hora de Criação",
    "Código externo", "Status", "Data de Perda/Ganho", "Hora de Perda/Ganho",
    "Motivo de perda", "Razão de Perda", "Data Venda  Agenda", "Data Proposta",
    "SDRResponsável", "DataApresentação1", "DataApresentação2", "Data UltContato",
    "Temperatura", "Horas", "Produtos", "Vlr Projeto", "Vlr Mensalidade", "qtde",
    "opportunity_updated_at",  # usado para controle de extração incremental
]

# Mapeamento dos custom_fields reais descobertos na plataforma
CF_OPORTUNIDADE = {
    "_data_agendamento":  "Data Venda  Agenda",
    "_data_apresentao1":  "DataApresentação1",
    "_data_apresentao2":  "DataApresentação2",
    "_data_proposta":     "Data Proposta",
    "_data_ult_contato":  "Data UltContato",
    "_horas":             "Horas",
    "_produtos":          "Produtos",
    "_s_d_r_responsvel":  "SDRResponsável",
    "_temperatura":       "Temperatura",
    "_vlr_mensalidade":   "Vlr Mensalidade",
    "_vlr_projeto":       "Vlr Projeto",
}

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _token() -> str:
    return os.environ.get("LEADS2B_TOKEN", TOKEN_V1)


def _headers() -> dict:
    return {"Authorization": f"Bearer {_token()}"}


def _get(endpoint: str, params: dict = None) -> dict:
    url = f"{BASE_URL}{endpoint}"
    resp = requests.get(url, headers=_headers(), params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _janelas(inicio: str, fim: str, dias: int = 30):
    """Gera pares (start, finish) em janelas de N dias.
    A API não pagina corretamente via offset, portanto cada janela deve
    caber em uma única página (<=100 registros).
    - oportunidades: dias=30 é suficiente (max ~87/mês)
    - leads: dias=7 é necessário (meses como Nov/24 têm 348 leads)
    """
    dt_ini = datetime.strptime(inicio, "%Y-%m-%d")
    dt_fim = datetime.strptime(fim,    "%Y-%m-%d")
    atual  = dt_ini
    while atual <= dt_fim:
        proximo = min(atual + timedelta(days=dias - 1), dt_fim)
        yield atual.strftime("%Y-%m-%d 00:00:00"), proximo.strftime("%Y-%m-%d 23:59:59")
        atual = proximo + timedelta(days=1)


def _buscar_paginas(endpoint: str, params_base: dict) -> list:
    """Percorre todas as páginas de um endpoint (result é lista).
    A API rejeita offset=0; primeira página não envia o parâmetro.
    O campo 'size' retorna a contagem da página atual (não o total),
    então a parada é feita quando a página retornar menos que LIMITE.
    """
    params  = dict(params_base)
    params["limit"] = LIMITE
    offset  = 0
    total   = []
    while True:
        p = dict(params)
        if offset > 0:
            p["offset"] = offset   # offset=0 é inválido na API
        data   = _get(endpoint, p)
        result = data.get("result", [])
        itens  = result if isinstance(result, list) else []
        if not itens:
            break
        total.extend(itens)
        if len(itens) < LIMITE:
            break   # última página — menos registros que o limite
        offset += LIMITE
        time.sleep(PAUSA)
    return total


# ---------------------------------------------------------------------------
# Cache de clientes
# ---------------------------------------------------------------------------
_cache_cli: dict[int, dict] = {}


def _cliente(customer_id) -> dict:
    if not customer_id:
        return {}
    cid = int(customer_id)
    if cid not in _cache_cli:
        try:
            data = _get("/customers/list", {"id": cid})
            result = data.get("result", {})
            clientes = (result.get("customers") or result) if isinstance(result, dict) else result
            _cache_cli[cid] = clientes[0] if clientes else {}
        except Exception:
            _cache_cli[cid] = {}
        time.sleep(PAUSA)
    return _cache_cli[cid]


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------

def _data(val) -> str:
    if not val:
        return ""
    try:
        dt = datetime.fromisoformat(str(val).replace("Z", ""))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(val)


def _hora(val) -> str:
    if not val:
        return ""
    try:
        dt = datetime.fromisoformat(str(val).replace("Z", ""))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return ""


def _tags(tags: list) -> str:
    return ";".join(t.get("name", "") for t in (tags or []) if t.get("name"))


def _produtos_nomes(items: list) -> str:
    return ";".join(i.get("name", "") for i in (items or []) if i.get("name"))


def _qtde(items: list):
    if not items:
        return ""
    try:
        total = sum(float(i.get("amount", 0)) for i in items)
        return total if total > 0 else ""
    except Exception:
        return ""


def _status_legivel(val: str) -> str:
    mapa = {"Em andamento": "Ativo", "active": "Ativo",
            "won": "Ganho", "lost": "Perdido",
            "Perdida": "Perdido", "Ganha": "Ganho"}
    return mapa.get(val or "", val or "")


# ---------------------------------------------------------------------------
# Mapeamento oportunidade → linha
# ---------------------------------------------------------------------------

def _mapear(op: dict, leads_por_id: dict) -> dict:
    cli = _cliente(op.get("customer_id"))
    cli_contatos = cli.get("contacts", []) or []
    contato_pri  = cli_contatos[0] if cli_contatos else {}

    # Lead vinculado (para Descrição e Título)
    op_id = str(op.get("opportunity_id", ""))
    lead  = leads_por_id.get(op_id, {})

    # Produtos: preferencia ao custom_field _produtos (texto livre); fallback para items
    cf = op.get("custom_fields") or {}
    produtos_cf  = cf.get("_produtos") or ""
    produtos_api = _produtos_nomes(op.get("items", []))
    produtos_val = produtos_cf or produtos_api

    # Valor total: usa opportunity_total_value se total_value for zero
    tv = op.get("total_value") or op.get("opportunity_total_value") or ""
    vlr_total = f"R$ {float(tv):.2f}" if tv and float(tv) > 0 else ""

    linha: dict = {
        "Responsável":               op.get("opportunity_responsible", ""),
        "ID Oportunidade":           op_id,
        "ID Cliente":                op.get("customer_id") or "",
        "ID Contato":                op.get("contact_list_id") or "",
        "Descrição":                 lead.get("body") or lead.get("interest") or "",
        "Razão social":              op.get("company_name") or cli.get("name", ""),
        "Título do negócio":         lead.get("lead_name") or lead.get("company_name") or "",
        "CNPJ":                      str(op.get("contact_cnpj") or cli.get("cnpj") or "").replace(".0",""),
        "Nome do Cliente":           cli.get("social_name") or cli.get("name", ""),
        "Nome do Contato":           op.get("contact_name", ""),
        "Telefone do Contato":       op.get("contact_phone") or contato_pri.get("phone", ""),
        "Celular do Contato":        contato_pri.get("cell_phone") or cli.get("cell_phone", ""),
        "E-mail do contato":         op.get("contact_email") or contato_pri.get("email", ""),
        "Grupo do cliente":          cli.get("group") or cli.get("customer_group") or "",
        "Contatos":                  ";".join(c.get("name","") for c in cli_contatos if c.get("name")),
        "Endereço":                  (op.get("contact_address") or op.get("customer_address")
                                      or cli.get("address") or ""),
        "Cidade":                    (op.get("contact_city") or op.get("customer_city")
                                      or cli.get("city") or ""),
        "Estado":                    (op.get("contact_state") or op.get("customer_state")
                                      or cli.get("state") or ""),
        "Origem":                    op.get("origin") or "",
        "Origem do cliente":         (cli.get("origin") or {}).get("name", ""),
        "Categoria do cliente":      (cli.get("category") or {}).get("name", ""),
        "TAGS":                      _tags(op.get("tags")),
        "Funil de vendas":           op.get("pipeline", ""),
        "Etapa do funil de vendas":  op.get("pipeline_step", ""),
        "Forma de Pagamento":        "",   # disponível em pedidos (endpoint /orders)
        "Data esperada de fechamento": _data(op.get("expected_close_date")),
        "Valor Total":               vlr_total,
        "Valor mensal":              cf.get("_vlr_mensalidade") or "",
        "Tempo como oportunidade":   op.get("days_in_pipeline") or "",
        "Criado por":                op.get("opportunity_created_by") or "",
        "Data de Criação":           _data(op.get("opportunity_created_at")),
        "Hora de Criação":           _hora(op.get("opportunity_created_at")),
        "Código externo":            op.get("fk_id") or op.get("rdstation_uuid") or "",
        "Status":                    _status_legivel(op.get("opportunity_status") or op.get("lead_status")),
        "Data de Perda/Ganho":       _data(op.get("lost_at") or op.get("won_at")),
        "Hora de Perda/Ganho":       _hora(op.get("lost_at") or op.get("won_at")),
        "Motivo de perda":           op.get("loss_reason") or "",
        "Razão de Perda":            op.get("loss_details") or "",
        "Data Venda  Agenda":        cf.get("_data_agendamento") or "",
        "Data Proposta":             cf.get("_data_proposta") or "",
        "SDRResponsável":            cf.get("_s_d_r_responsvel") or op.get("lead_responsible") or "",
        "DataApresentação1":         cf.get("_data_apresentao1") or "",
        "DataApresentação2":         cf.get("_data_apresentao2") or "",
        "Data UltContato":           cf.get("_data_ult_contato") or "",
        "Temperatura":               cf.get("_temperatura") or "",
        "Horas":                     cf.get("_horas") or "",
        "Produtos":                  produtos_val,
        "Vlr Projeto":               cf.get("_vlr_projeto") or vlr_total,
        "Vlr Mensalidade":           cf.get("_vlr_mensalidade") or "",
        "qtde":                      _qtde(op.get("items")),
        "opportunity_updated_at":    op.get("opportunity_updated_at") or "",
    }
    return linha


# ---------------------------------------------------------------------------
# Modo descoberta
# ---------------------------------------------------------------------------

def descobrir():
    print("Buscando 1 oportunidade para inspecionar campos...")
    hoje  = datetime.today()
    ini   = (hoje - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
    fim   = hoje.strftime("%Y-%m-%d 23:59:59")
    data  = _get("/opportunities/list", {"limit": 1, "start_at": ini, "finish_at": fim})
    result = data.get("result", [])
    ops  = result if isinstance(result, list) else []
    if not ops:
        print("Nenhuma oportunidade no último mês. Tente --desde com data mais antiga.")
        return
    op = ops[0]
    print("\n=== CAMPOS DA OPORTUNIDADE ===")
    print(json.dumps(op, indent=2, ensure_ascii=False))
    cf = op.get("custom_fields") or {}
    print("\n=== CUSTOM FIELDS (chaves reais) ===")
    for k, v in cf.items():
        print(f"  {k!r:35}  =>  {v!r}")


# ---------------------------------------------------------------------------
# Extração principal
# ---------------------------------------------------------------------------

def extrair(desde: str = None, ate: str = None, saida: str = None):
    ini = desde or "2024-11-01"
    fim = ate    or datetime.today().strftime("%Y-%m-%d")

    print(f"Extraindo oportunidades de {ini} a {fim} ...")

    # 1. Busca todas as oportunidades em janelas mensais (max ~87/mês, cabe em 1 página)
    oportunidades: list[dict] = []
    for start, finish in _janelas(ini, fim, dias=30):
        print(f"  janela {start[:10]} a {finish[:10]}")
        lote = _buscar_paginas("/opportunities/list", {"start_at": start, "finish_at": finish})
        oportunidades.extend(lote)
        time.sleep(PAUSA)

    # Remove duplicatas (mesmo id pode aparecer em janelas sobrepostas se updated_from for usado)
    vistos = set()
    unicos = []
    for op in oportunidades:
        oid = op.get("opportunity_id")
        if oid not in vistos:
            vistos.add(oid)
            unicos.append(op)
    oportunidades = unicos
    print(f"Total de oportunidades únicas: {len(oportunidades)}")

    if not oportunidades:
        print("Nenhuma oportunidade encontrada.")
        return None

    # 2. Busca leads para mapear Descrição e Título do negócio por opportunity_id
    print("Buscando leads (para Descrição e Título)...")
    leads_raw: list[dict] = []
    for start, finish in _janelas(ini, fim, dias=7):
        lote = _buscar_paginas("/leads/list", {"start_at": start, "finish_at": finish})
        leads_raw.extend(lote)
        time.sleep(PAUSA)

    leads_por_oportunidade: dict[str, dict] = {}
    for ld in leads_raw:
        oid = str(ld.get("opportunity_id") or "")
        if oid:
            leads_por_oportunidade[oid] = ld

    print(f"Leads carregados: {len(leads_raw)} | com opportunity_id: {len(leads_por_oportunidade)}")

    # 3. Monta linhas
    linhas = []
    for i, op in enumerate(oportunidades, 1):
        try:
            linhas.append(_mapear(op, leads_por_oportunidade))
        except Exception as exc:
            print(f"  Erro id={op.get('opportunity_id')}: {exc}")
        if i % 100 == 0:
            print(f"  Processadas {i}/{len(oportunidades)}...")

    # 4. DataFrame com colunas na ordem correta
    df = pd.DataFrame(linhas)
    for col in COLUNAS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS]

    # 5. Salva CSV
    if saida:
        caminho = Path(saida)
    else:
        DIR_SAIDA.mkdir(parents=True, exist_ok=True)
        caminho = DIR_SAIDA / "oportunidades_base.csv"

    df.to_csv(caminho, index=False, encoding="utf-8-sig")
    print(f"\nSalvo: {caminho}")
    print(f"Linhas: {len(df)} | Colunas: {len(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# Extração incremental de oportunidades (updated_from + janelas)
# ---------------------------------------------------------------------------

def extrair_incremental(saida: str = None):
    """Extrai apenas oportunidades atualizadas desde a última extração e faz merge."""

    caminho = Path(saida) if saida else DIR_SAIDA / "oportunidades_base.csv"

    # Se arquivo não existe ou não tem a coluna de controle → extração completa
    if not caminho.exists():
        print("Arquivo não encontrado. Realizando extração completa...")
        return extrair(saida=saida)

    df_existente = pd.read_csv(caminho, encoding="utf-8-sig", low_memory=False)

    if "opportunity_updated_at" not in df_existente.columns or df_existente["opportunity_updated_at"].isna().all():
        print("Coluna opportunity_updated_at ausente. Realizando extração completa...")
        return extrair(saida=saida)

    ultima = pd.to_datetime(df_existente["opportunity_updated_at"], errors="coerce").max()
    if pd.isna(ultima):
        print("Data de última atualização inválida. Realizando extração completa...")
        return extrair(saida=saida)

    # Recua 1 hora para garantir sobreposição e não perder registros no limite
    desde = (ultima - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    ate   = datetime.today().strftime("%Y-%m-%d")

    print(f"Extração incremental de oportunidades: updated_from={desde}")

    # Janelas de 1 dia com updated_from + finish_at para não perder registros se >100/dia
    oportunidades: list[dict] = []
    for start, finish in _janelas(desde[:10], ate, dias=1):
        start_ts  = start[:10] + " 00:00:00"
        finish_ts = finish[:10] + " 23:59:59"
        print(f"  janela {start_ts[:10]}")
        lote = _buscar_paginas("/opportunities/list", {
            "updated_from": start_ts,
            "finish_at":    finish_ts,
        })
        oportunidades.extend(lote)
        time.sleep(PAUSA)

    # Remove duplicatas
    vistos: set = set()
    unicos = []
    for op in oportunidades:
        oid = op.get("opportunity_id")
        if oid not in vistos:
            vistos.add(oid)
            unicos.append(op)

    print(f"Oportunidades com atualização: {len(unicos)}")

    if not unicos:
        print("Nenhuma atualização encontrada. Arquivo mantido.")
        return df_existente

    # Busca leads dos últimos 30 dias para título/descrição dos registros novos
    print("Buscando leads vinculados (últimos 30 dias)...")
    leads_raw: list[dict] = []
    ini_leads = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    for start, finish in _janelas(ini_leads, ate, dias=7):
        lote = _buscar_paginas("/leads/list", {"start_at": start, "finish_at": finish})
        leads_raw.extend(lote)
        time.sleep(PAUSA)

    leads_por_oportunidade: dict[str, dict] = {}
    for ld in leads_raw:
        oid = str(ld.get("opportunity_id") or "")
        if oid:
            leads_por_oportunidade[oid] = ld

    # Monta linhas novas/atualizadas
    linhas_novas = []
    for op in unicos:
        try:
            linhas_novas.append(_mapear(op, leads_por_oportunidade))
        except Exception as exc:
            print(f"  Erro id={op.get('opportunity_id')}: {exc}")

    df_novos = pd.DataFrame(linhas_novas)
    for col in COLUNAS:
        if col not in df_novos.columns:
            df_novos[col] = ""
    df_novos = df_novos[COLUNAS]

    # Merge: atualiza registros existentes pelo ID Oportunidade, adiciona novos
    df_base = df_existente.copy()
    for col in COLUNAS:
        if col not in df_base.columns:
            df_base[col] = ""

    ids_novos    = set(df_novos["ID Oportunidade"].astype(str))
    df_mantidos  = df_base[~df_base["ID Oportunidade"].astype(str).isin(ids_novos)]
    df_final     = pd.concat([df_mantidos, df_novos], ignore_index=True)
    df_final     = df_final[COLUNAS]

    df_final.to_csv(caminho, index=False, encoding="utf-8-sig")
    print(f"\nSalvo: {caminho}")
    print(f"Total linhas: {len(df_final)} | Atualizados/Adicionados: {len(linhas_novas)}")
    return df_final


# ---------------------------------------------------------------------------
# Leads — colunas e mapeamento
# ---------------------------------------------------------------------------

COLUNAS_LEADS = [
    "ID Lead", "Nome do Lead", "Razão Social", "CNPJ", "Contato Principal",
    "E-mail", "Telefone", "Cidade", "Estado", "CEP", "Bairro", "Complemento",
    "Origem", "Funil", "Etapa do Funil", "Status", "Responsável",
    "Data de Criação", "Hora de Criação", "Dias no Funil",
    "Data de Perda", "Motivo de Perda",
    "ID Oportunidade", "Status da Oportunidade", "Data da Oportunidade",
    "ID Cliente", "Nome do Cliente", "Razão Social Cliente",
    "Data do Pedido", "Valor do Pedido",
    "TAGS", "Código Externo", "ID Lista",
    "Atividade", "Faturamento", "Segmento", "Nome Completo", "Indique Ganhe",
]

# custom_fields reais do lead
CF_LEADS = {
    "_atividade":     "Atividade",
    "_faturamento":   "Faturamento",
    "_segmento":      "Segmento",
    "_nome_completo": "Nome Completo",
    "_indique_ganhe": "Indique Ganhe",
}

STATUS_LEAD = {
    "Em andamento":  "Em andamento",
    "Lead ganho":    "Ganho",
    "Lead perdido":  "Perdido",
    "active":        "Em andamento",
    "won":           "Ganho",
    "lost":          "Perdido",
}


def _mapear_lead(ld: dict) -> dict:
    cf = ld.get("custom_fields") or {}
    linha = {
        "ID Lead":                   ld.get("lead_id", ""),
        "Nome do Lead":              ld.get("lead_name", ""),
        "Razão Social":              ld.get("company_name", ""),
        "CNPJ":                      str(ld.get("cnpj") or "").replace(".0", ""),
        "Contato Principal":         ld.get("main_contact", ""),
        "E-mail":                    ld.get("main_email") or ld.get("email", ""),
        "Telefone":                  ld.get("main_phone") or ld.get("phone", ""),
        "Cidade":                    ld.get("city", ""),
        "Estado":                    ld.get("state", ""),
        "CEP":                       ld.get("zipcode", ""),
        "Bairro":                    ld.get("neighborhood", ""),
        "Complemento":               ld.get("complement", ""),
        "Origem":                    ld.get("origin", ""),
        "Funil":                     ld.get("pipeline", ""),
        "Etapa do Funil":            ld.get("pipeline_step", ""),
        "Status":                    STATUS_LEAD.get(ld.get("lead_status", ""), ld.get("lead_status", "")),
        "Responsável":               ld.get("lead_responsable", ""),
        "Data de Criação":           _data(ld.get("lead_created_at")),
        "Hora de Criação":           _hora(ld.get("lead_created_at")),
        "Dias no Funil":             ld.get("days_in_pipeline", ""),
        "Data de Perda":             _data(ld.get("lost_at")),
        "Motivo de Perda":           ld.get("loss_reason", ""),
        "ID Oportunidade":           ld.get("opportunity_id", ""),
        "Status da Oportunidade":    _status_legivel(ld.get("opportunity_status", "")),
        "Data da Oportunidade":      _data(ld.get("opportunity_created_at")),
        "ID Cliente":                ld.get("customer_id", ""),
        "Nome do Cliente":           ld.get("customer_name", ""),
        "Razão Social Cliente":      ld.get("customer_company_name", ""),
        "Data do Pedido":            _data(ld.get("order_date")),
        "Valor do Pedido":           ld.get("order_total", ""),
        "TAGS":                      _tags(ld.get("tags")),
        "Código Externo":            ld.get("fk_id", ""),
        "ID Lista":                  ld.get("list_id", ""),
        "Atividade":                 cf.get("_atividade", ""),
        "Faturamento":               cf.get("_faturamento", ""),
        "Segmento":                  cf.get("_segmento", ""),
        "Nome Completo":             cf.get("_nome_completo", ""),
        "Indique Ganhe":             cf.get("_indique_ganhe", ""),
    }
    return linha


# ---------------------------------------------------------------------------
# Prospects — colunas, mapeamento e extração
# ---------------------------------------------------------------------------

COLUNAS_PROSPECTS = [
    "ID Prospect", "Nome do Prospect", "Razão Social", "CNPJ",
    "Contato Principal", "E-mail", "Telefone", "Cidade", "Estado",
    "CEP", "Bairro", "Rua", "Complemento", "País",
    "Origem", "Funil", "Etapa do Funil", "Responsável",
    "Ativo", "Enriquecido", "Data de Enriquecimento",
    "Data de Criação", "Hora de Criação",
    "Data de Atualização", "Hora de Atualização",
    "Data de Perda", "Motivo de Perda",
    "TAGS", "Código Externo", "ID Lista", "Departamento",
    "Atividade", "Faturamento", "Segmento", "Nome Completo", "Indique Ganhe",
]

CF_PROSPECTS = {
    "_atividade":     "Atividade",
    "_faturamento":   "Faturamento",
    "_segmento":      "Segmento",
    "_nome_completo": "Nome Completo",
    "_indique_ganhe": "Indique Ganhe",
}


def _mapear_prospect(p: dict) -> dict:
    cf = p.get("custom_fields") or {}
    return {
        "ID Prospect":              p.get("prospect_id", ""),
        "Nome do Prospect":         p.get("prospect_name", ""),
        "Razão Social":             p.get("social_reason") or p.get("company_name", ""),
        "CNPJ":                     str(p.get("cnpj") or "").replace(".0", ""),
        "Contato Principal":        p.get("main_contact", ""),
        "E-mail":                   p.get("main_email") or p.get("email", ""),
        "Telefone":                 p.get("main_phone") or p.get("phone", ""),
        "Cidade":                   p.get("city", ""),
        "Estado":                   p.get("state", ""),
        "CEP":                      p.get("zipcode", ""),
        "Bairro":                   p.get("neighborhood", ""),
        "Rua":                      p.get("street", ""),
        "Complemento":              p.get("complement", ""),
        "País":                     p.get("country", ""),
        "Origem":                   p.get("origin", ""),
        "Funil":                    p.get("pipeline", ""),
        "Etapa do Funil":           p.get("pipeline_step", ""),
        "Responsável":              p.get("prospect_responsable", ""),
        "Ativo":                    p.get("active", ""),
        "Enriquecido":              p.get("enriched", ""),
        "Data de Enriquecimento":   _data(p.get("enriched_at")),
        "Data de Criação":          _data(p.get("created_at")),
        "Hora de Criação":          _hora(p.get("created_at")),
        "Data de Atualização":      _data(p.get("updated_at")),
        "Hora de Atualização":      _hora(p.get("updated_at")),
        "Data de Perda":            _data(p.get("lost_at")),
        "Motivo de Perda":          p.get("loss_reason", ""),
        "TAGS":                     _tags(p.get("tags")),
        "Código Externo":           p.get("fk_id", ""),
        "ID Lista":                 p.get("list_id", ""),
        "Departamento":             p.get("department", ""),
        "Atividade":                cf.get("_atividade", ""),
        "Faturamento":              cf.get("_faturamento", ""),
        "Segmento":                 cf.get("_segmento", ""),
        "Nome Completo":            cf.get("_nome_completo", ""),
        "Indique Ganhe":            cf.get("_indique_ganhe", ""),
    }


def extrair_prospects(desde: str = None, ate: str = None, saida: str = None):
    ini = desde or "2024-11-01"
    fim = ate    or datetime.today().strftime("%Y-%m-%d")

    print(f"Extraindo prospects de {ini} a {fim} ...")

    prospects_raw: list[dict] = []
    for start, finish in _janelas(ini, fim, dias=30):
        print(f"  janela {start[:10]} a {finish[:10]}")
        lote = _buscar_paginas("/prospect/list", {"start_at": start, "finish_at": finish})
        prospects_raw.extend(lote)
        time.sleep(PAUSA)

    vistos: set = set()
    unicos = []
    for p in prospects_raw:
        pid = p.get("prospect_id")
        if pid not in vistos:
            vistos.add(pid)
            unicos.append(p)

    print(f"Total de prospects unicos: {len(unicos)}")
    if not unicos:
        print("Nenhum prospect encontrado.")
        return None

    linhas = [_mapear_prospect(p) for p in unicos]

    df = pd.DataFrame(linhas)
    for col in COLUNAS_PROSPECTS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS_PROSPECTS]

    if saida:
        caminho = Path(saida)
    else:
        DIR_SAIDA.mkdir(parents=True, exist_ok=True)
        caminho = DIR_SAIDA / "prospects_base.csv"

    df.to_csv(caminho, index=False, encoding="utf-8-sig")
    print(f"\nSalvo: {caminho}")
    print(f"Linhas: {len(df)} | Colunas: {len(df.columns)}")
    return df


def descobrir_lead():
    print("Buscando 1 lead para inspecionar campos...")
    hoje = datetime.today()
    ini  = (hoje - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
    fim  = hoje.strftime("%Y-%m-%d 23:59:59")
    data = _get("/leads/list", {"limit": 1, "start_at": ini, "finish_at": fim})
    result = data.get("result", [])
    leads  = result if isinstance(result, list) else []
    if not leads:
        print("Nenhum lead no ultimo mes.")
        return
    ld = leads[0]
    print("\n=== CAMPOS DO LEAD ===")
    print(json.dumps(ld, indent=2, ensure_ascii=False))
    cf = ld.get("custom_fields") or {}
    print("\n=== CUSTOM FIELDS (chaves reais) ===")
    for k, v in cf.items():
        print(f"  {k!r:35}  =>  {v!r}")


def extrair_leads(desde: str = None, ate: str = None, saida: str = None):
    ini = desde or "2024-11-01"
    fim = ate    or datetime.today().strftime("%Y-%m-%d")

    print(f"Extraindo leads de {ini} a {fim} ...")

    leads_raw: list[dict] = []
    for start, finish in _janelas(ini, fim, dias=7):
        print(f"  janela {start[:10]} a {finish[:10]}")
        try:
            lote = _buscar_paginas("/leads/list", {"start_at": start, "finish_at": finish})
            leads_raw.extend(lote)
        except Exception as exc:
            print(f"  [AVISO] janela {start[:10]} a {finish[:10]} ignorada: {exc}")
        time.sleep(PAUSA)

    # Remove duplicatas por lead_id
    vistos: set = set()
    unicos = []
    for ld in leads_raw:
        lid = ld.get("lead_id")
        if lid not in vistos:
            vistos.add(lid)
            unicos.append(ld)

    print(f"Total de leads unicos: {len(unicos)}")
    if not unicos:
        print("Nenhum lead encontrado.")
        return None

    linhas = []
    for i, ld in enumerate(unicos, 1):
        try:
            linhas.append(_mapear_lead(ld))
        except Exception as exc:
            print(f"  Erro id={ld.get('lead_id')}: {exc}")
        if i % 200 == 0:
            print(f"  Processados {i}/{len(unicos)}...")

    df = pd.DataFrame(linhas)
    for col in COLUNAS_LEADS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS_LEADS]

    if saida:
        caminho = Path(saida)
    else:
        DIR_SAIDA.mkdir(parents=True, exist_ok=True)
        caminho = DIR_SAIDA / "leads_base.csv"

    df.to_csv(caminho, index=False, encoding="utf-8-sig")
    print(f"\nSalvo: {caminho}")
    print(f"Linhas: {len(df)} | Colunas: {len(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# Pós-vendas (after_sales) — colunas, mapeamento e extração
# ---------------------------------------------------------------------------

COLUNAS_POS_VENDAS = [
    "ID PosVenda", "Responsável", "Empresa", "CNPJ", "Contato",
    "E-mail", "Cidade", "Estado", "Funil", "Etapa do Funil",
    "Status", "Data de Criação", "Hora de Criação",
    "Data de Atualização", "Hora de Atualização",
    "Data de Perda/Ganho", "Motivo de Perda",
    "Valor Total", "Dias no Funil",
    "Data Proposta", "DataApresentação1", "DataApresentação2",
    "Data UltContato", "Temperatura", "Horas", "Produtos",
    "Vlr Projeto", "Vlr Mensalidade",
    "after_sale_updated_at",
]


def _mapear_pos_venda(as_: dict) -> dict:
    cf = as_.get("custom_fields") or {}
    tv = as_.get("after_sale_total_value") or ""
    try:
        vlr_total = f"R$ {float(tv):.2f}" if tv and float(tv) > 0 else ""
    except Exception:
        vlr_total = ""

    produtos_cf = cf.get("_produtos") or ""
    if isinstance(produtos_cf, list):
        partes = []
        for p in produtos_cf:
            if isinstance(p, dict):
                partes.append(p.get("label", ""))
            elif isinstance(p, str):
                partes.append(p)
        produtos_cf = ";".join(x for x in partes if x)

    return {
        "ID PosVenda":          as_.get("after_sale_id", ""),
        "Responsável":          as_.get("after_sale_responsible", ""),
        "Empresa":              as_.get("company_name", ""),
        "CNPJ":                 str(as_.get("contact_cnpj") or "").replace(".0", ""),
        "Contato":              as_.get("contact_name", ""),
        "E-mail":               as_.get("contact_email", ""),
        "Cidade":               as_.get("customer_city") or as_.get("contact_city", ""),
        "Estado":               as_.get("customer_state") or as_.get("contact_state", ""),
        "Funil":                as_.get("pipeline", ""),
        "Etapa do Funil":       as_.get("pipeline_step", ""),
        "Status":               _status_legivel(as_.get("after_sale_status", "")),
        "Data de Criação":      _data(as_.get("after_sale_created_at")),
        "Hora de Criação":      _hora(as_.get("after_sale_created_at")),
        "Data de Atualização":  _data(as_.get("after_sale_updated_at")),
        "Hora de Atualização":  _hora(as_.get("after_sale_updated_at")),
        "Data de Perda/Ganho":  _data(as_.get("lost_at") or as_.get("after_sale_processed_at")),
        "Motivo de Perda":      as_.get("loss_reason", ""),
        "Valor Total":          vlr_total,
        "Dias no Funil":        as_.get("days_in_pipeline", ""),
        "Data Proposta":        cf.get("_data_proposta", ""),
        "DataApresentação1":    cf.get("_data_apresentao1", ""),
        "DataApresentação2":    cf.get("_data_apresentao2", ""),
        "Data UltContato":      cf.get("_data_ult_contato", ""),
        "Temperatura":          cf.get("_temperatura", ""),
        "Horas":                cf.get("_horas", ""),
        "Produtos":             produtos_cf,
        "Vlr Projeto":          cf.get("_vlr_projeto", "") or vlr_total,
        "Vlr Mensalidade":      cf.get("_vlr_mensalidade", ""),
        "after_sale_updated_at": as_.get("after_sale_updated_at", ""),
    }


def extrair_pos_vendas(desde: str = None, ate: str = None, saida: str = None):
    ini = desde or "2024-11-01"
    fim = ate    or datetime.today().strftime("%Y-%m-%d")

    print(f"Extraindo pós-vendas de {ini} a {fim} ...")

    registros: list[dict] = []
    for start, finish in _janelas(ini, fim, dias=30):
        print(f"  janela {start[:10]} a {finish[:10]}")
        lote = _buscar_paginas("/after_sales/list", {"start_at": start, "finish_at": finish})
        registros.extend(lote)
        time.sleep(PAUSA)

    vistos: set = set()
    unicos = []
    for r in registros:
        rid = r.get("after_sale_id")
        if rid not in vistos:
            vistos.add(rid)
            unicos.append(r)

    print(f"Total de pós-vendas únicos: {len(unicos)}")
    if not unicos:
        print("Nenhum registro encontrado.")
        return None

    linhas = []
    for i, r in enumerate(unicos, 1):
        try:
            linhas.append(_mapear_pos_venda(r))
        except Exception as exc:
            print(f"  Erro id={r.get('after_sale_id')}: {exc}")
        if i % 100 == 0:
            print(f"  Processados {i}/{len(unicos)}...")

    df = pd.DataFrame(linhas)
    for col in COLUNAS_POS_VENDAS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS_POS_VENDAS]

    if saida:
        caminho = Path(saida)
    else:
        DIR_SAIDA.mkdir(parents=True, exist_ok=True)
        caminho = DIR_SAIDA / "pos_vendas_base.csv"

    df.to_csv(caminho, index=False, encoding="utf-8-sig")
    print(f"\nSalvo: {caminho}")
    print(f"Linhas: {len(df)} | Colunas: {len(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extrator Leads2b -> CSV")
    parser.add_argument("--entidade", choices=["oportunidades", "leads", "prospects", "pos_vendas"],
                        default="oportunidades",
                        help="Entidade a extrair (padrão: oportunidades)")
    parser.add_argument("--completo", action="store_true",
                        help="Força extração completa desde 2024-11-01 (ignora incremental)")
    parser.add_argument("--descobrir", action="store_true",
                        help="Mostra JSON bruto + custom_fields de 1 registro recente")
    parser.add_argument("--desde", metavar="YYYY-MM-DD", default=None,
                        help="Data inicial (padrão: 2024-11-01)")
    parser.add_argument("--ate", metavar="YYYY-MM-DD", default=None,
                        help="Data final (padrão: hoje)")
    parser.add_argument("--saida", metavar="ARQUIVO.csv", default=None,
                        help="Caminho do CSV de saida")
    parser.add_argument("--token", default=None,
                        help="Token JWT (substitui TOKEN_V1 no código)")
    args = parser.parse_args()

    if args.token:
        os.environ["LEADS2B_TOKEN"] = args.token

    if args.descobrir:
        if args.entidade == "leads":
            descobrir_lead()
        else:
            descobrir()
    elif args.entidade == "leads":
        extrair_leads(desde=args.desde, ate=args.ate, saida=args.saida)
    elif args.entidade == "prospects":
        extrair_prospects(desde=args.desde, ate=args.ate, saida=args.saida)
    elif args.entidade == "pos_vendas":
        extrair_pos_vendas(desde=args.desde, ate=args.ate, saida=args.saida)
    elif args.completo or args.desde:
        # --completo ou --desde força extração completa
        extrair(desde=args.desde, ate=args.ate, saida=args.saida)
    else:
        # Padrão: incremental se arquivo existir, completo se não existir
        extrair_incremental(saida=args.saida)


if __name__ == "__main__":
    main()
