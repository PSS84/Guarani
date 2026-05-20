"""
Apresentações e Propostas por Vendedor — mês atual
Entidades: Oportunidades + Pós-Vendas (after_sales)

Uso:
    python api/script_apr_proposta.py
    python api/script_apr_proposta.py --mes 04/2026
"""

import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "dados" / "api_leads2b"


def parse_mes(serie):
    s = serie.astype(str).str.strip().str[:10]
    return pd.to_datetime(s, dayfirst=True, errors="coerce").dt.to_period("M")


def contar(df, col_resp, col_ap1, col_ap2, col_prop, mes):
    ap1  = df[parse_mes(df[col_ap1])  == mes].groupby(col_resp).size().rename("Apresentação1")
    ap2  = df[parse_mes(df[col_ap2])  == mes].groupby(col_resp).size().rename("Apresentação2")
    prop = df[parse_mes(df[col_prop]) == mes].groupby(col_resp).size().rename("Propostas")
    return ap1, ap2, prop


def main():
    parser = argparse.ArgumentParser(description="Apresentações e Propostas por Vendedor")
    parser.add_argument("--mes", default=None, metavar="MM/YYYY",
                        help="Mês de referência (padrão: mês atual)")
    args = parser.parse_args()

    mes = args.mes or datetime.today().strftime("%m/%Y")
    try:
        periodo = pd.Period(datetime.strptime(mes, "%m/%Y"), freq="M")
    except ValueError:
        print(f"Formato de mês inválido: {mes}. Use MM/YYYY.")
        return

    df_op = pd.read_csv(BASE_DIR / "oportunidades_base.csv", encoding="utf-8-sig", low_memory=False)
    df_pv = pd.read_csv(BASE_DIR / "pos_vendas_base.csv",   encoding="utf-8-sig", low_memory=False)

    ap1_op, ap2_op, prop_op = contar(df_op, "Responsável", "DataApresentação1", "DataApresentação2", "Data Proposta", periodo)
    ap1_pv, ap2_pv, prop_pv = contar(df_pv, "Responsável", "DataApresentação1", "DataApresentação2", "Data Proposta", periodo)

    ap1  = ap1_op.add(ap1_pv,  fill_value=0)
    ap2  = ap2_op.add(ap2_pv,  fill_value=0)
    prop = prop_op.add(prop_pv, fill_value=0)

    resultado = pd.concat([ap1, ap2, prop], axis=1).fillna(0).astype(int)
    resultado["Total Apresentações"] = resultado["Apresentação1"] + resultado["Apresentação2"]
    resultado = resultado[["Apresentação1", "Apresentação2", "Total Apresentações", "Propostas"]]
    resultado = resultado.sort_values("Total Apresentações", ascending=False)

    totais = resultado.sum()
    totais.name = "TOTAL"
    resultado = pd.concat([resultado, totais.to_frame().T.astype(int)])

    mes_label = datetime.strptime(mes, "%m/%Y").strftime("%B/%Y").upper()
    print(f"\n=== {mes_label} — Oportunidades + Pós-Vendas ===\n")
    print(resultado.to_string())
    print()


if __name__ == "__main__":
    main()
