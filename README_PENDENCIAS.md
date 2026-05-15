# Pendencias — GitHub & Render

> Para cada nova pendencia: registrar aqui, confirmar com o usuario, executar e marcar como resolvido.
>
> **Status atual:** sem pendencias abertas. Registre aqui novas pendencias assim que surgirem.

---

## Como usar este arquivo

Quando for subir o ambiente ou surgir uma nova pendencia, envie para o assistente:
> "Leia o README_PENDENCIAS e me diga o que precisa ser feito."

O assistente ira listar cada pendencia, confirmar o que sera executado e resolver item por item.

---

## Logicas e Referencias

### Funil Deduplicado — Contagem unica entre entidades (Prospect → Lead → Oportunidade)

**Problema:** um registro pode existir nas tres entidades (prospect, lead, oportunidade) ao mesmo tempo.
Contar todas gera duplicidade. A logica abaixo garante contagem unica.

**Regra:**
- Quando um prospect e **ganho** → migrou para Lead. **Nao contar no prospect.**
- Quando um lead e **ganho** → migrou para Oportunidade. **Nao contar no lead.**
- Prospect **perdido ou em aberto** → nao migrou. **Contar no prospect.**
- Lead **perdido ou em aberto** → nao migrou. **Contar no lead.**
- Oportunidade em **qualquer status** (ativo, ganho, perdido) → **sempre contar.**

**Formula:**
```
Total unico = Prospects (perdidos + em aberto)
            + Leads (perdidos + em aberto)
            + Todas as oportunidades (ativo + ganho + perdido)
```

**Campos usados:**
- Prospect: coluna `Ativo` + `Data de Perda` (sem status direto na API)
- Lead: coluna `Status` (valores: Ganho, Perdido, Em andamento)
- Oportunidade: coluna `Status` (valores: Ativo, Ganho, Perdido)

> Implementado em 15/05/2026 no `diagnostico_prospecteleads.html` e no card Prospect do `dashboard_metas.html`. Ver secao abaixo para detalhes.

---

## Historico de pendencias resolvidas

### Dashboard Metas e Diagnostico Prospectos — 15/05/2026 ✅

| Item | Descricao | Status |
|---|---|---|
| 1 | Card Prospect (funil sem duplicados) com Inbound/Outbound no dashboard metas | ✅ Resolvido |
| 2 | Cobertura Individual movida para sidebar como anel "Recorrente" com delta vs meta | ✅ Resolvido |
| 3 | Reordenacao KPIs: Prospect, Apresentacoes, Propostas, Equipe | ✅ Resolvido |
| 4 | Reordenacao graficos: Apresentacoes, Propostas, Cob. Individual, Cob. Equipe | ✅ Resolvido |
| 5 | Alertas alinhados com contagem deduplicada da tabela de Pendencias | ✅ Resolvido |
| 6 | `dashboard_metas_teste.html` como sandbox local para testes antes de producao | ✅ Resolvido |
| 7 | `_processar_funil_mes()` no `app.py` retorna funil_mes no payload `/api/metas-vendedor` | ✅ Resolvido |
| 8 | Publicar `diagnostico_prospecteleads.html` e rotas `/guarani/crm/diagnostico` + `/api/diagnostico-prospectos` | ✅ Resolvido |
| 9 | Versionar `dados/api_leads2b/*.csv` no GitHub para o Render acessar | ✅ Resolvido |

**Observacoes:**
- `dashboard_metas_teste.html` serve como sandbox local — nao e necessario publicar no Render.
- Os CSVs da `api_leads2b/` precisam de commit manual a cada atualizacao via `leads2b_extrator.py`.
- Extrator de oportunidades ja usa modo incremental (`updated_from`) — leads e prospects ainda fazem extracao completa.

### Integracao API Leads2b — 13/05/2026 ✅

| Item | Descricao | Status |
|---|---|---|
| 1 | Ler e analisar documentacao da API Leads2b (PDF) | ✅ Resolvido |
| 2 | Criar script `api/leads2b_extrator.py` para extrair oportunidades e leads | ✅ Resolvido |
| 3 | Mapear custom_fields reais da plataforma | ✅ Resolvido — descobertos via `--descobrir` |
| 4 | Extrair historico completo (nov/2024 a mai/2026) | ✅ Resolvido — 543 oportunidades, 521 leads |

**Observacoes:**
- Script local apenas — nao faz parte do deploy no Render.
- O campo `Descricao` (notas do SDR) nao e retornado pela API v1.
- Dependencias locais necessarias: `requests` e `python-dateutil` (nao estao em `requirements.txt`).

### Dashboards comerciais e Instagram — 10/05/2026 ✅

| Item | Descricao | Status |
|---|---|---|
| 1 | Publicar dashboards Instagram geral e maio no Render | ✅ Resolvido — rotas `/guarani/crm/instagram` e `/guarani/crm/instagram/maio` |
| 2 | Publicar CSV de oportunidades usado pelas APIs Instagram | ✅ Resolvido — `dados/crmoportunidades-336.csv` versionado |
| 3 | Publicar dashboard de acompanhamento por vendedor Instagram | ✅ Resolvido — rota `/guarani/crm/instagram/vendedor` |
| 4 | Publicar dashboard de metas e ranking comercial | ✅ Resolvido — rotas `/guarani/vendas/metas`, `/guarani/vendas/ranking` e `/guarani/vendas/ranking_vendedor` |
| 5 | Publicar dados e imagens necessarios aos dashboards comerciais | ✅ Resolvido — `dados/Vendas2026.xlsx` e fotos dos vendedores em `dados/img/` |

**Observacoes:**
- `dados/img/meta.png` nao foi versionado porque nao sera usado no ranking atual.
- Enquanto `crmoportunidades-336.csv` e `Vendas2026.xlsx` forem fontes versionadas, atualizacoes de dados exigem novo commit/push para refletir no Render.

### Deploy inicial — 27/04/2026 ✅

| Item | Descricao | Status |
|---|---|---|
| 1 | PDFs linkados localmente no `manual-vendedor.html` | ✅ Resolvido — hospedados no Google Drive |
| 2 | Rota Flask para servir `material_de_apoio/` | ✅ Nao necessario — optado pelo Google Drive |
| 3 | Criar `render.yaml` | ✅ Criado na raiz do projeto |
| 4 | Revisar `.gitignore` | ✅ `material_de_apoio/` adicionado ao `.gitignore` |
| 5 | Secoes 19 e 20 com conteudo de arquivos locais | ✅ Sem acao necessaria para deploy |

**Arquivos hospedados no Google Drive:**
Pasta: `https://drive.google.com/drive/folders/1l4QEjtjEkS_LCvQDlqQRahQ8ld1VukD5`
Total: 16 PDFs + 1 PNG = 17 arquivos
