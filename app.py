import os
import sys
import glob
from datetime import date
from pathlib import Path
from collections import Counter

import pandas as pd
from flask import Flask, render_template, send_from_directory, jsonify, request

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "guarani" / "templates"
SCRIPT_DIR = BASE_DIR / "guarani" / "Script"
_dados_env = os.environ.get("GUARANI_DADOS_DIR")
DADOS_DIR = Path(_dados_env) if _dados_env else BASE_DIR / "dados"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from precos_2026 import carregar_precos_2026  # noqa: E402

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))


def _csv_instagram():
    """Retorna o CSV crmoportunidades mais recente em dados/."""
    arquivos = glob.glob(str(DADOS_DIR / "crmoportunidades*.csv"))
    if not arquivos:
        return None
    return max(arquivos, key=os.path.getmtime)


def _semanas_instagram(ig):
    """Agrega atividade semana a semana (segunda a domingo) para leads Instagram."""
    ig = ig.copy()

    def parse(col):
        return pd.to_datetime(ig[col], dayfirst=True, errors="coerce")

    ig["_dc"]  = parse("Data de Criação")
    ig["_da1"] = parse("DataApresentação1")
    ig["_da2"] = parse("DataApresentação2")
    ig["_dp"]  = parse("Data Proposta")
    ig["_dfg"] = parse("Data de Perda/Ganho")

    # Coleta todas as datas relevantes para definir o intervalo
    todas = pd.concat([ig["_dc"], ig["_da1"], ig["_da2"], ig["_dp"]]).dropna()
    if todas.empty:
        return []

    # Segunda-feira da primeira e última semana
    def proxima_segunda(dt):
        return dt - pd.Timedelta(days=dt.weekday())

    inicio = proxima_segunda(todas.min()).normalize()
    fim    = proxima_segunda(todas.max()).normalize()

    semanas = []
    atual = inicio
    while atual <= fim:
        fim_sem = atual + pd.Timedelta(days=6)

        novos = int(((ig["_dc"] >= atual) & (ig["_dc"] <= fim_sem)).sum())

        apres = int((
            ((ig["_da1"] >= atual) & (ig["_da1"] <= fim_sem)) |
            ((ig["_da2"] >= atual) & (ig["_da2"] <= fim_sem))
        ).sum())

        prop = int(((ig["_dp"] >= atual) & (ig["_dp"] <= fim_sem)).sum())

        ganhos = int(
            ((ig["Status"] == "Ganho") & (ig["_dfg"] >= atual) & (ig["_dfg"] <= fim_sem)).sum()
        )

        if novos or apres or prop or ganhos:
            semanas.append({
                "label":  f"{atual.strftime('%d/%m')}–{fim_sem.strftime('%d/%m')}",
                "inicio": atual.strftime("%Y-%m-%d"),
                "fim":    fim_sem.strftime("%Y-%m-%d"),
                "novos":  novos,
                "apresentacoes": apres,
                "propostas": prop,
                "ganhos": ganhos,
            })

        atual += pd.Timedelta(days=7)

    return semanas


def _perfis_instagram(df):
    """Agrupa leads por tag de perfil (Dentro Perfil / Fora Perfil / Perfil Indefinido)."""
    PERFIS = ["dentro perfil", "fora perfil", "perfil indefinido"]

    def detectar(tags_str):
        t = str(tags_str).lower()
        for p in PERFIS:
            if p in t:
                return p.title()
        return None

    df = df.copy()
    df["_perfil"] = df["TAGS"].fillna("").apply(detectar)
    perfil_df = df[df["_perfil"].notna()]
    result = []
    for perfil, grp in perfil_df.groupby("_perfil"):
        leads_list = []
        for _, row in grp.iterrows():
            titulo = row.get("Título do negócio") or row.get("Nome do Contato") or "—"
            tempo  = row.get("Tempo como oportunidade")
            leads_list.append({
                "titulo": str(titulo) if pd.notna(titulo) else "—",
                "status": str(row["Status"]),
                "tempo":  int(tempo) if pd.notna(tempo) else None,
            })
        result.append({
            "tag":     perfil,
            "total":   len(grp),
            "ativo":   int((grp["Status"] == "Ativo").sum()),
            "perdido": int((grp["Status"] == "Perdido").sum()),
            "ganho":   int((grp["Status"] == "Ganho").sum()),
            "leads":   leads_list,
        })
    result.sort(key=lambda x: x["total"], reverse=True)
    return result


def _propostas_ativas(df, incluir_vendedor=True):
    """Retorna leads com Status==Ativo e Data Proposta preenchida, ordenado por dias aguardando."""
    tem_proposta = df["Data Proposta"].notna()
    sub = df[(df["Status"] == "Ativo") & tem_proposta].copy()
    hoje = pd.Timestamp.today().normalize()
    sub["_dp"]  = pd.to_datetime(sub["Data Proposta"].str[:10],       format="%d/%m/%Y", errors="coerce")
    sub["_ult"] = pd.to_datetime(sub["Data UltContato"].str[:10],    format="%d/%m/%Y", errors="coerce")
    result = []
    for _, row in sub.iterrows():
        dp   = row["_dp"]
        dias = int((hoje - dp).days) if pd.notna(dp) else None
        item = {
            "id":            str(row.get("ID Oportunidade", "")),
            "titulo":        str(row.get("Título do negócio") or "—"),
            "data_proposta": dp.strftime("%d/%m/%Y") if pd.notna(dp) else "—",
            "dias_proposta": dias,
            "ult_contato":   row["_ult"].strftime("%d/%m/%Y") if pd.notna(row["_ult"]) else None,
        }
        if incluir_vendedor:
            item["vendedor"] = str(row.get("Responsável") or "—")
        result.append(item)
    result.sort(key=lambda x: x["dias_proposta"] if x["dias_proposta"] is not None else -1, reverse=True)
    return result


def _processar_instagram(csv_path, mes=None):
    """Processa leads Instagram do CSV. mes = 'YYYY-MM' para filtrar por mês de criação."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)

    ig = df[df["TAGS"].fillna("").str.contains("Instagram", case=False)].copy()

    if mes:
        ig["_criacao"] = pd.to_datetime(ig["Data de Criação"], dayfirst=True, errors="coerce")
        ig = ig[ig["_criacao"].dt.to_period("M").astype(str) == mes]

    total = len(ig)
    ativos = int((ig["Status"] == "Ativo").sum())
    perdidos = int((ig["Status"] == "Perdido").sum())
    ganhos = int((ig["Status"] == "Ganho").sum())

    tem_apres = ig["DataApresentação1"].notna() | ig["DataApresentação2"].notna()
    apresentacoes = int(tem_apres.sum())

    tem_proposta = ig["Data Proposta"].notna()
    propostas = int(tem_proposta.sum())
    negociacao_ativa = int(((ig["Status"] == "Ativo") & tem_proposta).sum())

    perdidos_df = ig[ig["Status"] == "Perdido"]
    perdidos_com_prop = ig[(ig["Status"] == "Perdido") & tem_proposta]

    def ranking(subset):
        contagem = Counter(
            m for m in subset["Motivo de perda"].dropna() if str(m).strip()
        )
        return [{"label": k, "n": v} for k, v in contagem.most_common()]

    return {
        "csv": os.path.basename(csv_path),
        "kpis": {
            "total": total,
            "ativos": ativos,
            "perdidos": perdidos,
            "ganhos": ganhos,
            "apresentacoes": apresentacoes,
            "propostas": propostas,
            "negociacao_ativa": negociacao_ativa,
        },
        "funil": [
            {"label": "Leads captados",       "value": total},
            {"label": "Apresentações feitas", "value": apresentacoes},
            {"label": "Propostas negociadas", "value": propostas},
            {"label": "Em negociação ativa",  "value": negociacao_ativa},
            {"label": "Contratos assinados",  "value": ganhos},
        ],
        "ranking_todos":    ranking(perdidos_df),
        "ranking_proposta": ranking(perdidos_com_prop),
        "total_perdidos":           len(perdidos_df),
        "total_perdidos_proposta":  len(perdidos_com_prop),
        "semanas": _semanas_instagram(ig),
        "mes": mes,
        "propostas_ativas": _propostas_ativas(ig),
        "perfis": _perfis_instagram(ig),
    }


def _processar_vendedor(csv_path, vendedor=None):
    df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
    ig = df[df["TAGS"].fillna("").str.contains("Instagram", case=False)].copy()

    vendedores = sorted(ig["Responsável"].dropna().unique().tolist())

    if not vendedor:
        return {"vendedores": vendedores, "csv": os.path.basename(csv_path)}

    vdf = ig[ig["Responsável"] == vendedor].copy()

    total    = len(vdf)
    ativos   = int((vdf["Status"] == "Ativo").sum())
    perdidos = int((vdf["Status"] == "Perdido").sum())
    ganhos   = int((vdf["Status"] == "Ganho").sum())

    tem_apres    = vdf["DataApresentação1"].notna() | vdf["DataApresentação2"].notna()
    apresentacoes = int(tem_apres.sum())
    tem_proposta  = vdf["Data Proposta"].notna()
    propostas     = int(tem_proposta.sum())
    negociacao_ativa = int(((vdf["Status"] == "Ativo") & tem_proposta).sum())

    perdidos_df      = vdf[vdf["Status"] == "Perdido"]
    perdidos_com_prop = vdf[(vdf["Status"] == "Perdido") & tem_proposta]

    def ranking(subset):
        c = Counter(m for m in subset["Motivo de perda"].dropna() if str(m).strip())
        return [{"label": k, "n": v} for k, v in c.most_common()]

    # Etapas do funil: ativos por etapa + ganhos na coluna 100%
    ativos_df = vdf[vdf["Status"] == "Ativo"]
    etapas_raw = ativos_df["Etapa do funil de vendas"].value_counts()
    funil_etapas = [{"etapa": k, "n": int(v)} for k, v in etapas_raw.items()]
    if ganhos > 0:
        funil_etapas.append({"etapa": "Ganho (100%)", "n": ganhos})

    # Propostas ativas
    propostas_ativas = _propostas_ativas(vdf, incluir_vendedor=False)

    # Perfil de leads Instagram (apenas leads com uma das 3 tags de perfil)
    PERFIS = ["dentro perfil", "fora perfil", "perfil indefinido"]

    def detectar_perfil(tags_str):
        t = str(tags_str).lower()
        for p in PERFIS:
            if p in t:
                return p.title()
        return None

    vdf["_perfil"] = vdf["TAGS"].fillna("").apply(detectar_perfil)
    perfil_df = vdf[vdf["_perfil"].notna()].copy()
    perfis_data = []
    for perfil, grp in perfil_df.groupby("_perfil"):
        leads = []
        for _, row in grp.iterrows():
            titulo = row.get("Título do negócio") or row.get("Nome do Contato") or "—"
            tempo  = row.get("Tempo como oportunidade")
            leads.append({
                "titulo": str(titulo) if pd.notna(titulo) else "—",
                "status": str(row["Status"]),
                "tempo":  int(tempo) if pd.notna(tempo) else None,
            })
        perfis_data.append({
            "tag":     perfil,
            "total":   len(grp),
            "ativo":   int((grp["Status"] == "Ativo").sum()),
            "perdido": int((grp["Status"] == "Perdido").sum()),
            "ganho":   int((grp["Status"] == "Ganho").sum()),
            "leads":   leads,
        })
    perfis_data.sort(key=lambda x: x["total"], reverse=True)

    # Eficiência comercial — tempos entre etapas
    def parse(col):
        return pd.to_datetime(vdf[col], dayfirst=True, errors="coerce")

    vdf["_dc"]  = parse("Data de Criação")
    vdf["_da1"] = parse("DataApresentação1")
    vdf["_dp"]  = parse("Data Proposta")
    vdf["_dfg"] = parse("Data de Perda/Ganho")

    def avg_dias(serie):
        s = serie.dropna()
        s = s[s >= 0]
        return round(float(s.mean()), 1) if len(s) > 0 else None

    tempo_op  = pd.to_numeric(vdf["Tempo como oportunidade"], errors="coerce")
    avg_op    = avg_dias(tempo_op)
    avg_apres = avg_dias((vdf["_da1"] - vdf["_dc"]).dt.days)
    avg_prop  = avg_dias((vdf["_dp"]  - vdf["_da1"]).dt.days)

    fechados  = vdf[vdf["Status"].isin(["Perdido", "Ganho"]) & vdf["_dp"].notna() & vdf["_dfg"].notna()]
    avg_fech  = avg_dias((fechados["_dfg"] - fechados["_dp"]).dt.days)

    return {
        "vendedores": vendedores,
        "vendedor":   vendedor,
        "csv":        os.path.basename(csv_path),
        "kpis": {
            "total": total, "ativos": ativos, "perdidos": perdidos, "ganhos": ganhos,
            "apresentacoes": apresentacoes, "propostas": propostas,
            "negociacao_ativa": negociacao_ativa,
        },
        "ranking_todos":           ranking(perdidos_df),
        "ranking_proposta":        ranking(perdidos_com_prop),
        "total_perdidos":          len(perdidos_df),
        "total_perdidos_proposta": len(perdidos_com_prop),
        "funil_etapas":            funil_etapas,
        "perfis":                  perfis_data,
        "propostas_ativas":        propostas_ativas,
        "eficiencia": {
            "tempo_medio_oportunidade": avg_op,
            "dias_ate_apresentacao":    avg_apres,
            "dias_ate_proposta":        avg_prop,
            "dias_ate_fechamento":      avg_fech,
        },
        "semanas": _semanas_instagram(vdf),
    }


def _processar_funil_mes(vendedor=None, mes=None, ano=None):
    """Funil sem duplicados (Prospects + Leads + Oportunidades) para o vendedor no mês."""
    from datetime import date as _date
    dir_api = BASE_DIR / "dados" / "api_leads2b"
    hoje = _date.today()
    mes = mes or hoje.month
    ano = ano or hoje.year
    META_LEADS = 150

    def _ler(nome):
        p = dir_api / nome
        if not p.exists():
            return pd.DataFrame()
        return pd.read_csv(p, encoding="utf-8-sig", low_memory=False)

    def _filtrar(df, col_data, col_resp):
        if df.empty:
            return df
        df = df.copy()
        df["_dt"] = pd.to_datetime(df[col_data], dayfirst=True, errors="coerce")
        mask = (df["_dt"].dt.month == mes) & (df["_dt"].dt.year == ano)
        if vendedor:
            primeiro = vendedor.split()[0].lower()
            mask &= df[col_resp].fillna("").str.lower().str.startswith(primeiro)
        return df[mask]

    KW_INBOUND = ["campanha", "site", "mkt", "inbound", "facebook", "marketing"]
    def _is_inbound(row):
        if str(row.get("Funil", "")).strip().lower() == "inbound":
            return True
        return any(kw in str(row.get("Origem", "")).lower() for kw in KW_INBOUND)

    df_p = _filtrar(_ler("prospects_base.csv"), "Data de Criação", "Responsável")
    if not df_p.empty and "Ativo" in df_p.columns:
        ativo  = df_p["Ativo"].astype(str).str.strip()
        perda  = df_p["Data de Perda"].fillna("").astype(str).str.strip() if "Data de Perda" in df_p.columns else pd.Series([""] * len(df_p))
        ganhou = (ativo == "0") & (perda == "")
        df_p   = df_p[~ganhou]

    df_l = _filtrar(_ler("leads_base.csv"), "Data de Criação", "Responsável")
    if not df_l.empty and "Status" in df_l.columns:
        df_l = df_l[df_l["Status"] != "Ganho"]

    df_o = _filtrar(_ler("oportunidades_base.csv"), "Data de Criação", "Responsável")

    def _cnt_inbound(df):
        if df.empty:
            return 0, 0
        ib = df.apply(_is_inbound, axis=1)
        return int(ib.sum()), int((~ib).sum())

    p_ib, p_ob = _cnt_inbound(df_p)
    l_ib, l_ob = _cnt_inbound(df_l)
    o_ib, o_ob = _cnt_inbound(df_o)

    total_p  = len(df_p)
    total_l  = len(df_l)
    total_o  = len(df_o)
    total    = total_p + total_l + total_o
    inbound  = p_ib + l_ib + o_ib
    outbound = p_ob + l_ob + o_ob

    return {
        "total":         total,
        "prospects":     total_p,
        "leads":         total_l,
        "oportunidades": total_o,
        "inbound":       inbound,
        "outbound":      outbound,
        "meta":          META_LEADS,
        "pct_meta":      round((total / META_LEADS) * 100, 1) if META_LEADS else 0,
        "mes":           mes,
        "ano":           ano,
        "disponivel":    (dir_api / "leads_base.csv").exists(),
    }


def _processar_metas(vendedor=None):
    planilha = BASE_DIR / "dados" / "Vendas2026.xlsx"
    df = pd.read_excel(planilha, sheet_name="QtdeMetas")
    df2026 = df[df["Ano"] == 2026].dropna(subset=["Vendedor"]).copy()
    df2026.columns = df2026.columns.astype(str).str.strip()
    df2026["Mês"] = pd.to_datetime(df2026["Mês"])

    def col_meta(df_in, *names):
        for n in names:
            if n in df_in.columns:
                return n
        return None

    vendedores = sorted(df2026["Vendedor"].unique().tolist())
    if not vendedor:
        return {"vendedores": vendedores}

    vdf = df2026[df2026["Vendedor"] == vendedor].sort_values("Mês")
    MESES_PT = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

    def pct(val):
        v = float(val) if pd.notna(val) else 0
        return round(v * 100, 1)

    def vals_named(*names):
        c = col_meta(vdf, *names)
        if not c:
            return [0.0] * len(vdf)
        return [float(v) if pd.notna(v) else 0 for v in vdf[c]]

    # Cobertura equipe (gráfico): fração ×100 no pct(). OBEquipe em milhares (ex.: 26 → 26.000).
    # Até abril/2026: ((Meta/(OBEquipe×1000))/3)×3 — de maio/2026 em diante: ((Meta/(OBEquipe×1000))/4)×4.
    # (Numericamente equivale a Meta/(OBEquipe×1000); mantemos N conforme regra de negócio.)
    meta_equipe_col = col_meta(df2026, "Meta Equipe", "Meta equipe")
    obequipe_col = col_meta(df2026, "OBEquipe", "OBEEquipe", "OBE Equipe")
    if not meta_equipe_col or not obequipe_col:
        raise ValueError("Planilha QtdeMetas: exige colunas 'Meta Equipe' e 'OBEquipe'.")

    def _divisor_equipe_mes(ts) -> int:
        if pd.isna(ts):
            return 3
        y, mo = int(ts.year), int(ts.month)
        if y < 2026:
            return 3
        if y == 2026 and mo <= 4:
            return 3
        return 4

    break_meta = []
    break_obe = []
    for ts in vdf["Mês"]:
        sl = df2026.loc[df2026["Mês"] == ts]
        if len(sl):
            break_meta.append(float(sl[meta_equipe_col].iloc[0]))
            break_obe.append(float(sl[obequipe_col].iloc[0]))
        else:
            break_meta.append(0.0)
            break_obe.append(0.0)

    def _pct_equipe_formula(me: float, oq: float, ts) -> float:
        if oq <= 0:
            return 0.0
        d = float(_divisor_equipe_mes(ts))
        frac = (float(me) / (float(oq) * 1000.0) / d) * d
        return pct(frac)

    pendencias = []

    # Fonte 1 — Vendas2026.xlsx aba "2026": contratos pendentes do vendedor
    try:
        vendas = pd.read_excel(planilha, sheet_name="2026")
        vendas.columns = vendas.columns.astype(str).str.strip()
        primeiro = vendedor.split()[0].lower()
        v_mask = vendas["Vendedor"].fillna("").str.lower().str.startswith(primeiro)
        pend_v = vendas[
            v_mask &
            (vendas["Contrato"].fillna("").str.strip().str.lower() == "pendente")
        ]
        def _data_contrato_celula(row):
            for col in ("Data Contrato", "Data do contrato", "Data"):
                if col not in row.index:
                    continue
                v = row[col]
                if pd.isna(v):
                    continue
                s = str(v).strip()
                if s and s.lower() != "nan":
                    return v
            return None

        for _, row in pend_v.iterrows():
            dt_raw = _data_contrato_celula(row)
            dt_parsed = pd.to_datetime(dt_raw, dayfirst=True, errors="coerce") if dt_raw is not None else pd.NaT
            dt_str = dt_parsed.strftime("%d/%m/%Y") if pd.notna(dt_parsed) else "—"
            dias_ctr = None
            if pd.notna(dt_parsed):
                hoje = date.today()
                d0 = dt_parsed.date() if hasattr(dt_parsed, "date") else dt_parsed
                dias_ctr = int((hoje - d0).days)
                if dias_ctr < 0:
                    dias_ctr = 0
            pendencias.append({
                "origem":    "contrato",
                "titulo":    str(row.get("Cliente") or "—"),
                "data":      dt_str,
                "dias":      dias_ctr,
                "produto":   str(row.get("Produto") or "—"),
            })
    except Exception:
        pass

    # Fonte 2 — CRM: leads Instagram com Perfil Indefinido, ativos, do vendedor
    try:
        csv_path = _csv_instagram()
        if csv_path:
            crm = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
            primeiro = vendedor.split()[0].lower()
            crm_v = crm[crm["Responsável"].fillna("").str.lower().str.startswith(primeiro)]
            tags = crm_v["TAGS"].fillna("").str.lower()
            mask = (
                (crm_v["Status"] == "Ativo") &
                tags.str.contains("instagram", case=False) &
                tags.str.contains("perfil indefinido", case=False)
            )
            for _, row in crm_v[mask].iterrows():
                dc = str(row.get("Data de Criação") or "")[:10]
                try:
                    dc_fmt = pd.to_datetime(dc, dayfirst=True, errors="coerce")
                    dc = dc_fmt.strftime("%d/%m/%Y") if pd.notna(dc_fmt) else dc
                except Exception:
                    pass
                tempo = row.get("Tempo como oportunidade")
                pendencias.append({
                    "origem":  "crm",
                    "titulo":  str(row.get("Título do negócio") or row.get("Nome do Contato") or "—"),
                    "data":    dc or "—",
                    "dias":    int(tempo) if pd.notna(tempo) else None,
                    "produto": "Instagram · Perfil Indefinido",
                })
    except Exception:
        pass

    obi_ind_col = col_meta(vdf, "OBI", "Obi")
    if not obi_ind_col:
        raise ValueError("Planilha QtdeMetas: coluna OBI não encontrada.")

    return {
        "dashboard_payload_ver": 5,  # mantido para compatibilidade; não utilizado pelo front
        "vendedor": vendedor,
        "vendedores": vendedores,
        "meses": [MESES_PT[m.month] for m in vdf["Mês"]],
        "cobertura_individual": [pct(v) for v in vdf[obi_ind_col]],
        "cobertura_equipe": [
            _pct_equipe_formula(m, o, ts) for m, o, ts in zip(break_meta, break_obe, vdf["Mês"])
        ],
        "equipe_breakdown": {
            "meta_equipe": break_meta,
            "obequipe_milhares": break_obe,
            "equipe_divisor": [_divisor_equipe_mes(ts) for ts in vdf["Mês"]],
        },
        "apresentacao":         vals_named("Apresentação", "Apresentacao"),
        "apresentacao_ob":      vals_named("OB Apresentação", "OB Apresentacao"),
        "proposta":             vals_named("Propsota", "Proposta"),
        "proposta_ob":          vals_named("OB Proposta ", "OB Proposta"),
        "pendencias":           pendencias,
        "total_contratos_pendentes": sum(1 for p in pendencias if p["origem"] == "contrato"),
        "total_perfil_indef":        sum(1 for p in pendencias if p["origem"] == "crm"),
        "funil_mes":                 _processar_funil_mes(vendedor=vendedor),
    }


def _processar_ranking(mes=None, ano: int = 2026):
    """
    Ranking da equipe em um mês: cobertura individual, apresentações, propostas,
    contratos (aba 2026). Cobertura e evolução usam Meta Individual × OBI da QtdeMetas:
    percentual = (OBI × Meta Individual) / Meta Individual × 100 (= OBI×100 quando Meta>0).
    """
    MESES_PT = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez",
    }

    planilha = BASE_DIR / "dados" / "Vendas2026.xlsx"
    df = pd.read_excel(planilha, sheet_name="QtdeMetas")
    df.columns = df.columns.astype(str).str.strip()
    df_y = df[(df["Ano"] == ano)].dropna(subset=["Vendedor"]).copy()
    df_y["Mês"] = pd.to_datetime(df_y["Mês"])

    meses_disp = sorted(df_y["Mês"].dt.month.unique().tolist())

    if mes is None and meses_disp:
        mes = meses_disp[-1]
    elif mes is None:
        mes = date.today().month

    if df_y.empty:
        return {
            "mes": mes,
            "ano": ano,
            "mes_label": MESES_PT.get(mes, ""),
            "meses_disponiveis": [],
            "evolucao_mes_referencia": None,
            "evolucao_ano_referencia": None,
            "ranking": [],
        }

    def pct_val(val):
        v = float(val) if pd.notna(val) else 0
        return round(v * 100, 1)

    def col(df_in, *names):
        for n in names:
            if n in df_in.columns:
                return n
        return None

    ap_col = col(df_y, "Apresentação", "Apresentacao")
    pr_col = col(df_y, "Propsota", "Proposta")
    obi_col = col(df_y, "OBI")
    meta_ind_col = col(df_y, "Meta Individual", "Meta individual")

    def cobertura_pct_meta_row(row) -> float:
        """% realizado vs meta individual do mês (OBI como fração da meta na planilha)."""
        obi_frac = float(row[obi_col]) if obi_col and pd.notna(row[obi_col]) else 0.0
        if meta_ind_col and meta_ind_col in row.index and pd.notna(row[meta_ind_col]):
            m = float(row[meta_ind_col])
            if m > 0:
                realiz = obi_frac * m
                return round((realiz / m) * 100.0, 1)
        return round(obi_frac * 100.0, 1)

    alvo = df_y[df_y["Mês"].dt.month == mes]
    if alvo.empty and meses_disp:
        mes = meses_disp[-1]
        alvo = df_y[df_y["Mês"].dt.month == mes]

    contratos_pv = {}
    try:
        vendas = pd.read_excel(planilha, sheet_name="2026")
        vendas.columns = vendas.columns.astype(str).str.strip()
        dc_col = col(vendas, "Data Contrato", "Data do contrato", "Data")
        if dc_col:
            dtc = pd.to_datetime(vendas[dc_col], dayfirst=True, errors="coerce")
            vendas["_vm"] = dtc.dt.month
            vendas["_vy"] = dtc.dt.year
            vm = vendas[(vendas["_vm"] == mes) & (vendas["_vy"] == ano)]
            for nome in alvo["Vendedor"].unique():
                primeiro = str(nome).split()[0].lower()
                mask = vm["Vendedor"].fillna("").str.lower().str.startswith(primeiro)
                contratos_pv[str(nome)] = int(mask.sum())
    except Exception:
        for nome in alvo["Vendedor"].unique():
            contratos_pv[str(nome)] = 0

    alvo = alvo.sort_values(obi_col or "OBI", ascending=False)

    # Evolução: sempre mês civil imediatamente anterior (ex.: Abr/2026 vs Mar/2026).
    # Janeiro compara com dezembro do ano anterior na QtdeMetas.
    mes_ref_evol = None
    ano_ref_evol = None
    cobertura_mes_anterior = {}
    prev_rows = None
    if mes > 1:
        mes_ref_evol = mes - 1
        ano_ref_evol = ano
        prev_rows = df_y[df_y["Mês"].dt.month == mes_ref_evol]
    else:
        prev_year = ano - 1
        df_prev = df[(df["Ano"] == prev_year)].dropna(subset=["Vendedor"]).copy()
        if not df_prev.empty:
            df_prev["Mês"] = pd.to_datetime(df_prev["Mês"])
            prev_rows = df_prev[df_prev["Mês"].dt.month == 12]
            if prev_rows is not None and not prev_rows.empty:
                mes_ref_evol = 12
                ano_ref_evol = prev_year
    if prev_rows is not None and not prev_rows.empty and mes_ref_evol is not None:
        for _, row in prev_rows.iterrows():
            vn = str(row["Vendedor"])
            cobertura_mes_anterior[vn] = cobertura_pct_meta_row(row)
    else:
        mes_ref_evol = None
        ano_ref_evol = None

    ranking = []
    for _, row in alvo.iterrows():
        nome = str(row["Vendedor"])
        ap = row[ap_col] if ap_col else None
        pr = row[pr_col] if pr_col else None
        ap_n = int(round(float(ap))) if ap is not None and pd.notna(ap) else 0
        ct = contratos_pv.get(nome, 0)
        cov = cobertura_pct_meta_row(row)
        meta_val = None
        if meta_ind_col and meta_ind_col in row.index and pd.notna(row[meta_ind_col]):
            meta_val = round(float(row[meta_ind_col]), 2)
        if ap_n > 0:
            conv = round((ct / ap_n) * 100, 1)
        else:
            conv = 0.0
        prev_cov = cobertura_mes_anterior.get(nome)
        if prev_cov is not None:
            evol = round(cov - prev_cov, 1)
        else:
            evol = None
        ranking.append(
            {
                "vendedor": nome,
                "meta_individual": meta_val,
                "cobertura_individual": cov,
                "apresentacoes": ap_n,
                "propostas": int(round(float(pr))) if pr is not None and pd.notna(pr) else 0,
                "contratos": ct,
                "conversao_pct": conv,
                "evolucao_pp": evol,
            }
        )

    return {
        "mes": mes,
        "ano": ano,
        "mes_label": MESES_PT.get(mes, ""),
        "meses_disponiveis": meses_disp,
        "evolucao_mes_referencia": mes_ref_evol,
        "evolucao_ano_referencia": ano_ref_evol,
        "ranking": ranking,
    }


@app.route("/dados/img/<path:filename>")
def dados_img(filename):
    return send_from_directory(str(BASE_DIR / "dados" / "img"), filename)


@app.route("/guarani/vendas/metas")
def dashboard_metas():
    resp = send_from_directory(str(BASE_DIR / "guarani" / "vendas"), "dashboard_metas.html")
    resp.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    return resp


@app.route("/api/metas-vendedor")
def api_metas_vendedor():
    try:
        vendedor = request.args.get("vendedor")
        payload = _processar_metas(vendedor=vendedor)
        resp = jsonify(payload)
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        return resp
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@app.route("/guarani/vendas/ranking")
@app.route("/guarani/vendas/ranking_vendedor")
def ranking_vendedor_page():
    return send_from_directory(str(BASE_DIR / "guarani" / "vendas"), "ranking_vendedor.html")


@app.route("/guarani/vendas/static/<path:filename>")
def vendas_static_files(filename):
    """PNG/CSS da página de ranking (arte + assets na pasta vendas)."""
    if ".." in filename or filename.startswith(("/", "\\")):
        return ("", 404)
    return send_from_directory(str(BASE_DIR / "guarani" / "vendas"), filename)


@app.route("/api/ranking-vendedores")
def api_ranking_vendedores():
    try:
        mes = request.args.get("mes", type=int)
        ano = request.args.get("ano", default=2026, type=int)
        return jsonify(_processar_ranking(mes=mes, ano=ano))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@app.route("/guarani/crm/instagram/vendedor")
def dashboard_vendedor_instagram():
    return send_from_directory(
        str(BASE_DIR / "guarani" / "crm"),
        "acompanhar_vendedor_campanha_instagram.html"
    )


@app.route("/api/instagram-vendedor")
def api_instagram_vendedor():
    csv_path = _csv_instagram()
    if not csv_path:
        return jsonify({"erro": "Nenhum arquivo crmoportunidades*.csv encontrado em dados/"}), 404
    try:
        vendedor = request.args.get("vendedor")
        return jsonify(_processar_vendedor(csv_path, vendedor=vendedor))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@app.route("/")
def home():
    return (
        "DT_Claude online. Acesse "
        "<a href='/guarani/precos'>/guarani/precos</a> para ver a tabela de precos."
    )


@app.route("/guarani/precos")
def pagina_precos():
    planilha = BASE_DIR / "dados" / "TABELA 2026.xlsx"
    erro = None
    secoes = []
    total_itens = 0

    try:
        dados = carregar_precos_2026(planilha)
        secoes = dados["secoes"]
        total_itens = dados["total_itens"]
    except Exception as exc:
        erro = f"Nao foi possivel carregar a planilha: {exc}"

    return render_template(
        "precos_2026.html",
        planilha_relativa="dados/TABELA 2026.xlsx (aba 2026)",
        secoes=secoes,
        total_itens=total_itens,
        erro=erro,
    )


@app.route("/guarani/crm/instagram")
def dashboard_instagram():
    return send_from_directory(
        str(BASE_DIR / "guarani" / "crm"),
        "dashboard_instagram.html"
    )


@app.route("/guarani/crm/instagram/maio")
def dashboard_instagram_maio():
    return send_from_directory(
        str(BASE_DIR / "guarani" / "crm"),
        "dashboard_instagram_maio.html"
    )


@app.route("/api/instagram-data")
def api_instagram_data():
    csv_path = _csv_instagram()
    if not csv_path:
        return jsonify({"erro": "Nenhum arquivo crmoportunidades*.csv encontrado em dados/"}), 404
    try:
        mes = request.args.get("mes")  # ex: "2026-05"
        dados = _processar_instagram(csv_path, mes=mes)
        return jsonify(dados)
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@app.route("/guarani/rh/integracao/manual-vendedor")
def manual_vendedor():
    return send_from_directory(
        str(BASE_DIR / "guarani" / "rh" / "integracao"),
        "manual-vendedor.html"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
