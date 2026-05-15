# Pasta `guarani/`

Modulo principal do projeto: scripts, templates HTML e recursos por area (RH, CRM, vendas, etc.).

## Subpastas

| Pasta | Conteudo | Versionado |
|---|---|---|
| `Script/` | `precos_2026.py` — le `TABELA 2026.xlsx` e prepara dados para exibicao | Sim |
| `templates/` | `precos_2026.html` — layout executivo da tabela de precos | Sim |
| `vendas/` | `dashboard_metas.html`, `dashboard_metas_teste.html`, `ranking_vendedor.html` | Sim |
| `crm/` | Dashboards Instagram (geral, maio, por vendedor) + diagnostico prospecteleads | Sim |
| `rh/integracao/` | Manual do vendedor, gerar_pdf.py, material_de_apoio/ | Parcial |
| `base/` | `clientes.html` | Nao |
| `campanhas/` | Analises locais de campanhas Instagram | Nao |
| `supervisor/` | Relatorios locais de acompanhamento comercial | Nao |

## Vendas (HTML + API)

- **Metas:** `vendas/dashboard_metas.html` — rota `/guarani/vendas/metas`, dados em `/api/metas-vendedor`.
  - Card Prospect (funil sem duplicados) com Inbound/Outbound na primeira posicao do KPI row.
  - Cobertura Individual na sidebar como anel "Recorrente" com delta vs meta e tendencia mensal.
  - Ordem KPIs: Prospect → Apresentacoes → Propostas → Cobertura Equipe.
  - Ordem graficos: Apresentacoes → Propostas → Cobertura Individual → Cobertura Equipe.
  - Alertas usam contagem deduplicada de pendencias (alinhada com a tabela de Pendencias).
- **Metas (teste):** `vendas/dashboard_metas_teste.html` — rota `/guarani/vendas/metas-teste`. Sandbox local para testar mudancas antes de aplicar em producao.
- **Ranking:** `vendas/ranking_vendedor.html` — rotas `/guarani/vendas/ranking` e `/guarani/vendas/ranking_vendedor`, dados em `/api/ranking-vendedores`.
- **Estaticos:** arquivos na propria pasta `vendas/` expostos via `/guarani/vendas/static/<nome>`.

## CRM / Instagram (HTML + API)

- **Dashboard geral:** `crm/dashboard_instagram.html` — rota `/guarani/crm/instagram`, dados em `/api/instagram-data`.
- **Dashboard Maio/2026:** `crm/dashboard_instagram_maio.html` — rota `/guarani/crm/instagram/maio`, dados em `/api/instagram-data?mes=2026-05`.
- **Acompanhamento por vendedor:** `crm/acompanhar_vendedor_campanha_instagram.html` — rota `/guarani/crm/instagram/vendedor`, dados em `/api/instagram-vendedor`.
- **Diagnostico Prospectos/Leads:** `crm/diagnostico_prospecteleads.html` — rota `/guarani/crm/diagnostico`, dados em `/api/diagnostico-prospectos`.
  - Funil sem duplicados (Prospect + Lead + Oportunidade), Inbound/Outbound por mes, por responsavel, sub-categorias e filtros de periodo/vendedor.
  - Fonte: `dados/api_leads2b/*.csv` (versionados no GitHub desde 15/05/2026).

## Dados — API Leads2b

Pasta `dados/api_leads2b/` — CSVs extraidos pela API Leads2b via `api/leads2b_extrator.py`:

| Arquivo | Conteudo |
|---|---|
| `prospects_base.csv` | Todos os prospects extraidos da API |
| `leads_base.csv` | Todos os leads extraidos da API |
| `oportunidades_base.csv` | Todas as oportunidades (historico completo) |

- Atualizacao local: rodar `python api/leads2b_extrator.py` (incremental para oportunidades, completo para leads e prospects).
- Apos atualizar, fazer commit e push para refletir no Render.
- Fonte anterior (CRM Instagram): `dados/crmoportunidades-336.csv` — mantido para compatibilidade com os dashboards Instagram.

## RH / Integracao

- `manual-vendedor.html`: manual estrategico do Executivo de Vendas, 27 secoes em 5 grupos. Publicado em `/guarani/rh/integracao/manual-vendedor`.
- `gerar_pdf.py`: gera `manual-vendedor.pdf` via Playwright (local, nao versionado).
- `material_de_apoio/`: PDFs e imagens de treinamento hospedados no Google Drive (local, nao versionado, em `.gitignore`).

Documentacao completa: `README.md` na raiz do repositorio.
