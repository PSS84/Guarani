# Pendências para Subir o Ambiente — GitHub & Render

> Antes de publicar o projeto, leia este arquivo e confirme cada item com o usuário.
> Para cada pendência: confirmar o que será feito, executar e marcar como resolvido.

---

## 1. PDFs, Imagens e Arquivos do Material de Apoio

**Situação:** Os arquivos do diretório `guarani/rh/integracao/material_de_apoio/` estão linkados no `manual-vendedor.html` com caminhos relativos locais. Eles **não sobem para o GitHub** e **não funcionam no Render** dessa forma.

**O que precisa ser feito:**
- Decidir onde hospedar os arquivos:
  - **Opção A — Google Drive:** Criar pasta `material_de_apoio`, subir os arquivos, compartilhar como público e substituir todos os links no HTML pelas URLs diretas do Drive.
  - **Opção B — Render (servidor):** Adicionar rota no `app.py` para servir via `send_from_directory` e subir os arquivos junto ao repositório.
- Atualizar todos os links no `manual-vendedor.html` com as URLs correspondentes à opção escolhida.

**Arquivos envolvidos:**
- `guarani/rh/integracao/manual-vendedor.html` — seções com links para `material_de_apoio/`
- `guarani/rh/integracao/material_de_apoio/` — arquivos locais

**Lista completa de arquivos que precisam ser hospedados:**

*Seção 09 · Material de Apoio — PDFs (10 arquivos):*
1. `[Guarani] Matrizes Comerciais ... v1 - 1. Encaixe Problema-Solução (PSF).pdf`
2. `[Guarani] Matrizes Comerciais ... v1 - 2. SPIN Selling.pdf`
3. `[Guarani] Matrizes Comerciais ... v1 - 3. Qualificação Pré-Vendas.pdf`
4. `[Guarani] Matrizes Comerciais ... v1 - 4. Objeção.pdf`
5. `Spin Selling - Alcançando Excelência Em Vendas - Neil Rackham.pdf`
6. `[Guarani Sistemas] 4 pilares principais de uma estrutura de ligação.pptx.pdf`
7. `[Guarani Sistemas] Investigação (SPIN Selling).pptx.pdf`
8. `[Guarani Sistemas] Demonstração de Capacidade.pptx.pdf`
9. `[Guarani] Script de Cold Call .pdf`
10. `[Guarani Sistemas] Processo de Follow Up - Atualizado.pdf`

*Seção 12 · Tarefas — Produtos Fase Inicial (2 arquivos):*
11. `GuaraniAFV.pdf`
12. `GuaraniB2B.pdf`

*Seção 22 · Estrutura de Vendas (2 arquivos):*
13. `02-Estrutura de Vendas.pdf`
14. `02-Estrutura de Vendas.png` *(imagem exibida na seção)*

*Seção 26 · Apresentações e Propostas (3 arquivos):*
15. `GuaraniBI.pdf`
16. `PROPOSTACLOUDICUS.pdf`
17. `PropostaERP2026.pdf`

> **Total: 16 PDFs + 1 PNG = 17 arquivos**

---

## 2. Rota Flask para servir arquivos (Opção B — Render)

**Situação:** Se decidir manter os arquivos no próprio Render (em vez de hospedagem externa), o `app.py` precisará de uma rota para servir os arquivos do `material_de_apoio`.

**O que precisa ser feito:**
- Adicionar a seguinte rota no `app.py`:

```python
@app.route("/guarani/rh/integracao/material_de_apoio/<path:filename>")
def material_de_apoio(filename):
    return send_from_directory(
        str(BASE_DIR / "guarani" / "rh" / "integracao" / "material_de_apoio"),
        filename
    )
```

**Arquivo envolvido:**
- `app.py`

---

## 3. Arquivo render.yaml

**Situação:** O projeto não possui o arquivo `render.yaml`, que conecta formalmente o projeto ao Render (define serviço, build command, start command).

**O que precisa ser feito:**
- Criar o `render.yaml` na raiz do projeto com o seguinte conteúdo:

```yaml
services:
  - type: web
    name: guarani
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
```

**Arquivo a criar:**
- `render.yaml` (raiz do projeto)

---

## 4. Verificar .gitignore

**Situação:** Confirmar se os PDFs e arquivos binários estão corretamente listados no `.gitignore`.

**O que precisa ser feito:**
- **Se escolher Opção A (Google Drive):** garantir que `material_de_apoio/` está no `.gitignore` — os arquivos ficam no Drive, não no repo.
- **Se escolher Opção B (Render):** remover `material_de_apoio/` do `.gitignore` para que os arquivos subam junto ao repositório.

**Arquivo envolvido:**
- `.gitignore`

---

## 5. Seções com conteúdo baseado em arquivos locais (referência interna)

**Situação:** As seções abaixo foram criadas com base em arquivos do `material_de_apoio` que **não estão diretamente linkados no HTML**, mas cujo conteúdo foi incorporado manualmente. Não há links a corrigir, mas é importante saber a origem caso precise atualizar o conteúdo futuramente.

| Seção HTML | Arquivo de origem |
|---|---|
| 19 · Qualificação de Lead | `Formulário de Qualificação AFV.xlsx` |
| 20 · PIC — Perfil Ideal do Cliente | `07 - PIC - Perfil Ideal Cliente.pdf` |

**O que precisa ser feito:**
- Nenhuma ação imediata para o deploy.
- Se esses arquivos forem atualizados no futuro, rever as seções 19 e 20 do `manual-vendedor.html`.

---

## Como usar este arquivo

Quando for subir o ambiente, envie para o assistente:
> "Leia o README_PENDENCIAS e me diga o que precisa ser feito."

O assistente irá listar cada pendência, confirmar o que será executado e resolver item por item.
