from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import pandas as pd
from markupsafe import Markup


SHEET_NAME = "2026"

PALETA = {
    "blue": {"fill": "#E6F1FB", "text": "#0C447C", "border": "#B5D4F4"},
    "green": {"fill": "#EAF3DE", "text": "#27500A", "border": "#C0DD97"},
    "amber": {"fill": "#FAEEDA", "text": "#633806", "border": "#FAC775"},
    "purple": {"fill": "#EEEDFE", "text": "#3C3489", "border": "#CECBF6"},
}

COR_POR_SECAO = {
    "PRODUTOS": "blue",
    "ADICIONAIS DIRETO ERP": "green",
    "ADICIONAIS INDIRETO ERP": "amber",
    "ADICIONAIS DIRETO AFV (PLUGIN)": "purple",
}


def _to_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return text


def _to_number(value: Any) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _muted_dash() -> Markup:
    return Markup('<span class="muted">—</span>')


def _fmt_brl(valor: float | None) -> Markup:
    if valor is None:
        return _muted_dash()
    if valor == 0:
        return _muted_dash()
    texto = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return Markup(texto)


def _fmt_horas(h: Any) -> Markup:
    if h is None:
        return _muted_dash()
    if isinstance(h, (int, float)) and not isinstance(h, bool):
        if h == 0:
            return _muted_dash()
        if float(h).is_integer():
            return Markup(f"{int(h)}h")
        return Markup(f"{h}h")
    texto = _to_text(h)
    if not texto:
        return _muted_dash()
    if texto in {"0", "0.0"}:
        return _muted_dash()
    return Markup(f'<span class="proj">{html.escape(texto)}</span>')


def _fmt_qtd(valor_bruto: Any, texto: str) -> Markup:
    num = _to_number(valor_bruto)
    if num is None:
        if not texto:
            return _muted_dash()
        return Markup(html.escape(texto))
    if num == 0:
        return _muted_dash()
    if num.is_integer():
        return Markup(str(int(num)))
    return Markup(str(num))


def _fmt_setup(valor_bruto: Any, texto: str) -> Markup:
    num = _to_number(valor_bruto)
    if num is None:
        if not texto:
            return _muted_dash()
        return Markup(html.escape(texto))
    return _fmt_brl(num)


def _fmt_mensalidade(valor_bruto: Any, texto: str) -> Markup:
    num = _to_number(valor_bruto)
    if num is None:
        if not texto:
            return _muted_dash()
        return Markup(html.escape(texto))
    return _fmt_brl(num)


def _fmt_info(texto: str) -> Markup:
    if not texto:
        return _muted_dash()
    return Markup(html.escape(texto))


def carregar_precos_2026(planilha: Path) -> dict[str, Any]:
    if not planilha.exists():
        raise FileNotFoundError(f"Planilha nao encontrada: {planilha}")

    df = pd.read_excel(planilha, sheet_name=SHEET_NAME, header=None)

    secoes: list[dict[str, Any]] = []
    secao_atual: dict[str, Any] | None = None
    linha_cabecalho_esperada = {
        "PRODUTOS",
        "ADICIONAIS DIRETO ERP",
        "ADICIONAIS INDIRETO ERP",
        "ADICIONAIS DIRETO AFV (PLUGIN)",
    }

    for _, row in df.iterrows():
        col_1 = _to_text(row.iloc[1] if len(row) > 1 else "")
        col_2 = _to_text(row.iloc[2] if len(row) > 2 else "")
        col_3 = _to_text(row.iloc[3] if len(row) > 3 else "")
        col_4 = _to_text(row.iloc[4] if len(row) > 4 else "")
        col_5 = _to_text(row.iloc[5] if len(row) > 5 else "")
        col_6 = _to_text(row.iloc[6] if len(row) > 6 else "")

        if not col_1:
            continue

        upper = col_1.upper()

        if upper in linha_cabecalho_esperada:
            cor = COR_POR_SECAO.get(upper, "blue")
            secao_atual = {"titulo": col_1, "cor": cor, "paleta": PALETA[cor], "itens": []}
            secoes.append(secao_atual)
            continue

        if upper.startswith("OBSERVA") or upper.startswith("INFORMATIVO GERAL"):
            secao_atual = None
            continue

        if secao_atual is None:
            continue

        qtd_num = _to_number(row.iloc[2] if len(row) > 2 else None)
        cdu_num = _to_number(row.iloc[3] if len(row) > 3 else None)
        mensalidade_num = _to_number(row.iloc[5] if len(row) > 5 else None)
        horas_tem_valor = bool(col_4)
        tem_numerico = qtd_num is not None or cdu_num is not None or mensalidade_num is not None
        is_subtitulo = not (tem_numerico or horas_tem_valor)

        if is_subtitulo:
            item = {
                "is_subtitulo": True,
                "produto_html": Markup(html.escape(col_1)),
            }
        else:
            horas_valor = row.iloc[4] if len(row) > 4 else None
            if horas_tem_valor and _to_number(horas_valor) is None:
                horas_fmt = _fmt_horas(col_4)
            else:
                horas_fmt = _fmt_horas(_to_number(horas_valor))

            item = {
                "is_subtitulo": False,
                "produto_html": Markup(html.escape(col_1)),
                "qtde_html": _fmt_qtd(row.iloc[2] if len(row) > 2 else None, col_2),
                "setup_html": _fmt_setup(row.iloc[3] if len(row) > 3 else None, col_3),
                "horas_html": horas_fmt,
                "mensalidade_html": _fmt_mensalidade(row.iloc[5] if len(row) > 5 else None, col_5),
                "info_html": _fmt_info(col_6),
            }
        secao_atual["itens"].append(item)

    total_itens = sum(len(secao["itens"]) for secao in secoes)
    return {"secoes": secoes, "total_itens": total_itens}
