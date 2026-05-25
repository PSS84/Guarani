"""
Atualiza os 4 arquivos CSV da pasta api_leads2b em sequência.

Uso:
    python atualizar_tudo.py

Equivale a rodar:
    python leads2b_extrator.py                        # oportunidades (incremental)
    python leads2b_extrator.py --entidade leads
    python leads2b_extrator.py --entidade prospects
    python leads2b_extrator.py --entidade pos_vendas
"""

from leads2b_extrator import (
    extrair_incremental,
    extrair_leads,
    extrair_prospects,
    extrair_pos_vendas,
)

ETAPAS = [
    ("Oportunidades (incremental)", extrair_incremental, {}),
    ("Leads",                        extrair_leads,       {}),
    ("Prospects",                    extrair_prospects,   {}),
    ("Pós-Vendas",                   extrair_pos_vendas,  {}),
]

def main():
    total = len(ETAPAS)
    for i, (nome, func, kwargs) in enumerate(ETAPAS, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{total}] {nome}")
        print('='*60)
        try:
            func(**kwargs)
        except Exception as exc:
            print(f"ERRO em {nome}: {exc}")

    print(f"\n{'='*60}")
    print("Atualização concluída!")
    print('='*60)

if __name__ == "__main__":
    main()
