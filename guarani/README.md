# Pasta `guarani/`

Modulo principal do projeto: scripts, templates HTML e recursos por area (RH, CRM, vendas, etc.).

## Subpastas

| Pasta | Conteudo | Versionado |
|---|---|---|
| `Script/` | `precos_2026.py` — le `TABELA 2026.xlsx` e prepara dados para exibicao | Sim |
| `templates/` | `precos_2026.html` — layout executivo da tabela de precos | Sim |
| `vendas/` | `dashboard_metas.html`, `ranking_vendedor.html` | Sim |
| `crm/` | Dashboards Instagram (geral, maio, por vendedor) | Sim |
| `rh/integracao/` | Manual do vendedor, gerar_pdf.py, material_de_apoio/ | Parcial |
| `base/` | `clientes.html` | Nao |
| `campanhas/` | Analises locais de campanhas Instagram | Nao |
| `supervisor/` | Relatorios locais de acompanhamento comercial | Nao |

## Vendas (HTML + API)

- **Metas:** `vendas/dashboard_metas.html` — rota `/guarani/vendas/metas`, dados em `/api/metas-vendedor`.
- **Ranking:** `vendas/ranking_vendedor.html` — rotas `/guarani/vendas/ranking` e `/guarani/vendas/ranking_vendedor`, dados em `/api/ranking-vendedores`.
- **Estaticos:** arquivos na propria pasta `vendas/` expostos via `/guarani/vendas/static/<nome>`.

## CRM / Instagram (HTML + API)

- **Dashboard geral:** `crm/dashboard_instagram.html` — rota `/guarani/crm/instagram`, dados em `/api/instagram-data`.
- **Dashboard Maio/2026:** `crm/dashboard_instagram_maio.html` — rota `/guarani/crm/instagram/maio`, dados em `/api/instagram-data?mes=2026-05`.
- **Acompanhamento por vendedor:** `crm/acompanhar_vendedor_campanha_instagram.html` — rota `/guarani/crm/instagram/vendedor`, dados em `/api/instagram-vendedor`.
- **Fonte atual:** `dados/crmoportunidades-336.csv` versionado no GitHub. Atualizacoes exigem novo commit para refletir no Render.
- **Fonte futura:** API Leads2b via `api/leads2b_extrator.py` (local) — substituira o CSV manual.

## RH / Integracao

- `manual-vendedor.html`: manual estrategico do Executivo de Vendas, 27 secoes em 5 grupos. Publicado em `/guarani/rh/integracao/manual-vendedor`.
- `gerar_pdf.py`: gera `manual-vendedor.pdf` via Playwright (local, nao versionado).
- `material_de_apoio/`: PDFs e imagens de treinamento hospedados no Google Drive (local, nao versionado, em `.gitignore`).

Documentacao completa: `README.md` na raiz do repositorio.
