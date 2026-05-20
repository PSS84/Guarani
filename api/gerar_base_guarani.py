"""
Gera guarani/base/base_guarani.html
Lê MapaOportunidadeClientesBaseGuarani.xlsm (sheet Clientes, 214 linhas, 85 colunas)
Todos os campos visíveis na tabela com sort e filtro por coluna.
"""

import json
import openpyxl
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

COLUNAS = [
    "QTDE",                        # 0
    "ID",                          # 1
    "IMPLANTADO",                  # 2
    "CNPJ PRINCIPAL",              # 3
    "CNPJ 1",                      # 4
    "CNPJ 2",                      # 5
    "CNPJ 3",                      # 6
    "CNPJ 4",                      # 7
    "CNPJ 5",                      # 8
    "CNPJ 6",                      # 9
    "CNPJ 7",                      # 10
    "CNPJ 8",                      # 11
    "CNPJ 9",                      # 12
    "CNPJ 10",                     # 13
    "CNPJ 11",                     # 14
    "CNPJ 12",                     # 15
    "CNPJ 13",                     # 16
    "CONTRATANTE",                 # 17
    "RAZÃO",                       # 18
    "CLIENTE",                     # 19
    "VIP",                         # 20
    "VENDEDOR",                    # 21
    "RESPONSÁVEL",                 # 22
    "DATA ASSINATURA CONTRATO",    # 23
    "ATIVO",                       # 24
    "CIDADE",                      # 25
    "UF",                          # 26
    "LOGRADOURO",                  # 27
    "BAIRRO",                      # 28
    "CEP",                         # 29
    "NOME SÓCIO",                  # 30
    "EMAIL SÓCIO",                 # 31
    "WHATSAPP SÓCIO",              # 32
    "NOME DECISOR",                # 33
    "E-MAIL DECISOR",              # 34
    "WHATSAPP DECISOR",            # 35
    "NOME USUÁRIO CHAVE",          # 36
    "E-MAIL USUÁRIO CHAVE",        # 37
    "WHATSAPP USUÁRIO CHAVE",      # 38
    "MÓDULO GUARANI ERP",          # 39
    "MÓDULO GUARANI AFV",          # 40
    "MÓDULO GUARANI BI",           # 41
    "MÓDULO GUARANI B2B",          # 42
    "MÓDULO GUARANI CLOUD",        # 43
    "ADDON ERP PCP",               # 44
    "ADDON ERP WMS",               # 45
    "ADDON ERP MDFE",              # 46
    "ADDON ERP TELEMARKETING",     # 47
    "ADDON ERP CONTÁBIL",          # 48
    "ADDON ERP CIAP",              # 49
    "ADDON ERP MDE",               # 50
    "ALIANÇA ERP CONCIL",          # 51
    "ALIANÇA ERP ROUTEASY",        # 52
    "ALIANÇA ERP PDV",             # 53
    "ALIANÇA ERP PLUGGTO",         # 54
    "ALIANÇA ERP TRAY",            # 55
    "ADDON ERP IMPORTAÇÃO XML",    # 56
    "ADDON ERP LINK PAGAMENTO",    # 57
    "ALIANÇA ERP KONCILI",         # 58
    "ADDON ERP BOLETO WHATSAPP",   # 59
    "ADDON ERP CTE",               # 60
    "ALIANÇA ERP JETCOMMERCE",     # 61
    "ADDON AFV PESQUISA MERCADO",  # 62
    "ADDON AFV ORÇAMENTO WEB",     # 63
    "ADDON AFV AGENDA",            # 64
    "ADDON AFV IARA",              # 65
    "ADDON AFV MULTILOJAS",        # 66
    "ADDON AFV LOJA B2B",          # 67
    "ADDON AFV PROPOSTA WEB",      # 68
    "GUARANI PDV MARKET",          # 69
    "QTDE USUÁRIO ERP",            # 70
    "QTDE GUARANI B2B",            # 71
    "QTDE GUARANI BI",             # 72
    "QTDE USUÁRIO AFV",            # 73
    "QTDE USUÁRIO AFV PREPOSTO",   # 74
    "QTDE USUÁRIO WMS",            # 75
    "QTDE USUÁRIO PDV",            # 76
    "QTDE USUÁRIO TELEMARKETING",  # 77
    "TS CLOUD",                    # 78
    "QTDE USUÁRIO CONTÁBIL",       # 79
    "SEGMENTO",                    # 80
    "RAMO ATIVIDADE",              # 81
    "SITE/REDES SOCIAIS",          # 82
    "BÔNUS",                       # 83
    "COUNT",                       # 84
]

BOOL_COLS = {
    "IMPLANTADO","VIP","ATIVO",
    "MÓDULO GUARANI ERP","MÓDULO GUARANI AFV","MÓDULO GUARANI BI",
    "MÓDULO GUARANI B2B","MÓDULO GUARANI CLOUD",
    "ADDON ERP PCP","ADDON ERP WMS","ADDON ERP MDFE","ADDON ERP TELEMARKETING",
    "ADDON ERP CONTÁBIL","ADDON ERP CIAP","ADDON ERP MDE",
    "ADDON ERP IMPORTAÇÃO XML","ADDON ERP LINK PAGAMENTO",
    "ADDON ERP BOLETO WHATSAPP","ADDON ERP CTE",
    "ALIANÇA ERP CONCIL","ALIANÇA ERP ROUTEASY","ALIANÇA ERP PDV",
    "ALIANÇA ERP PLUGGTO","ALIANÇA ERP TRAY","ALIANÇA ERP KONCILI",
    "ALIANÇA ERP JETCOMMERCE",
    "ADDON AFV PESQUISA MERCADO","ADDON AFV ORÇAMENTO WEB","ADDON AFV AGENDA",
    "ADDON AFV IARA","ADDON AFV MULTILOJAS","ADDON AFV LOJA B2B",
    "ADDON AFV PROPOSTA WEB","GUARANI PDV MARKET",
}

# Colunas com dropdown de valores únicos
DROPDOWN_COLS = {"UF","VENDEDOR","RESPONSÁVEL","SEGMENTO","RAMO ATIVIDADE","CIDADE","CONTRATANTE"}

DEFAULT_VIS = {
    "ID","RAZÃO","CNPJ PRINCIPAL","IMPLANTADO","ATIVO","VIP","VENDEDOR","RESPONSÁVEL",
    "DATA ASSINATURA CONTRATO","CIDADE","UF",
    "NOME SÓCIO","EMAIL SÓCIO","WHATSAPP SÓCIO",
    "NOME DECISOR","E-MAIL DECISOR","WHATSAPP DECISOR",
    "NOME USUÁRIO CHAVE","E-MAIL USUÁRIO CHAVE","WHATSAPP USUÁRIO CHAVE",
    "MÓDULO GUARANI ERP","MÓDULO GUARANI AFV","MÓDULO GUARANI BI","MÓDULO GUARANI B2B","MÓDULO GUARANI CLOUD",
    "ADDON ERP PCP","ADDON ERP WMS","ADDON ERP MDFE","ADDON ERP TELEMARKETING","ADDON ERP CONTÁBIL",
    "ADDON ERP CIAP","ADDON ERP MDE","ADDON ERP IMPORTAÇÃO XML","ADDON ERP LINK PAGAMENTO",
    "ADDON ERP BOLETO WHATSAPP","ADDON ERP CTE",
    "ALIANÇA ERP CONCIL","ALIANÇA ERP ROUTEASY","ALIANÇA ERP PDV","ALIANÇA ERP PLUGGTO",
    "ALIANÇA ERP TRAY","ALIANÇA ERP KONCILI","ALIANÇA ERP JETCOMMERCE",
    "ADDON AFV PESQUISA MERCADO","ADDON AFV ORÇAMENTO WEB","ADDON AFV AGENDA",
    "ADDON AFV IARA","ADDON AFV MULTILOJAS","ADDON AFV LOJA B2B","ADDON AFV PROPOSTA WEB",
    "GUARANI PDV MARKET",
    "QTDE USUÁRIO ERP","QTDE GUARANI B2B","QTDE GUARANI BI","QTDE USUÁRIO AFV",
    "QTDE USUÁRIO AFV PREPOSTO","QTDE USUÁRIO WMS","QTDE USUÁRIO PDV",
    "QTDE USUÁRIO TELEMARKETING","TS CLOUD","QTDE USUÁRIO CONTÁBIL",
    "SEGMENTO","RAMO ATIVIDADE","SITE/REDES SOCIAIS","BÔNUS","COUNT","QTDE",
    "CONTRATANTE","CLIENTE","LOGRADOURO","BAIRRO","CEP",
}


def val(v):
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v).strip()


def ler_dados():
    path = BASE / "dados" / "base" / "MapaOportunidadeClientesBaseGuarani.xlsm"
    wb = openpyxl.load_workbook(str(path), read_only=True, keep_vba=True, data_only=True)
    ws = wb["Clientes"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    dados = []
    for row in rows[1:]:
        if all(c is None for c in row):
            continue
        rec = {COLUNAS[i]: val(row[i]) for i in range(min(len(COLUNAS), len(row)))}
        dados.append(rec)
    return dados


def gerar_html(dados):
    n = len(dados)
    json_dados    = json.dumps(dados,             ensure_ascii=False)
    json_colunas  = json.dumps(COLUNAS,           ensure_ascii=False)
    json_bool     = json.dumps(list(BOOL_COLS),   ensure_ascii=False)
    json_dropdown = json.dumps(list(DROPDOWN_COLS), ensure_ascii=False)
    json_default  = json.dumps(list(DEFAULT_VIS), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Base Guarani — Clientes</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Inter',sans-serif;background:#f4f6f9;color:#1a2332;padding:20px}}

  /* ── HEADER ── */
  .header{{background:#1a2332;color:#fff;padding:16px 22px;border-radius:10px;margin-bottom:14px;
           display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}}
  .header h1{{font-size:16px;font-weight:600;letter-spacing:.3px}}
  .badge{{background:#3b82f6;color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:500}}

  /* ── TOOLBAR ── */
  .toolbar{{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}}
  .search-box{{flex:1;min-width:200px;padding:8px 12px;border:1px solid #dde3ec;border-radius:8px;
               font-size:13px;font-family:inherit;outline:none;transition:border .2s}}
  .search-box:focus{{border-color:#3b82f6}}
  .btn{{padding:8px 13px;border:1px solid #dde3ec;border-radius:8px;font-size:12px;
        font-family:inherit;background:#fff;cursor:pointer;color:#475569;white-space:nowrap;
        display:flex;align-items:center;gap:5px;transition:all .15s}}
  .btn:hover{{background:#f0f7ff;border-color:#3b82f6;color:#3b82f6}}
  .btn.on{{background:#3b82f6;color:#fff;border-color:#3b82f6}}
  .count{{font-size:12px;color:#64748b;margin-bottom:8px}}

  /* ── PAINEL COLUNAS ── */
  .col-panel{{display:none;background:#fff;border:1px solid #dde3ec;border-radius:10px;
              padding:14px 18px;margin-bottom:10px;box-shadow:0 2px 10px rgba(0,0,0,.06)}}
  .col-panel.open{{display:block}}
  .col-panel h3{{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;
                 letter-spacing:.5px;margin-bottom:10px}}
  .col-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:5px}}
  .col-item{{display:flex;align-items:center;gap:6px;font-size:12px;cursor:pointer;
             padding:3px 6px;border-radius:5px}}
  .col-item:hover{{background:#f1f5f9}}
  .col-item input{{cursor:pointer;accent-color:#3b82f6}}

  /* ── TABELA ── */
  .table-wrap{{overflow:auto;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.08);
               max-height:calc(100vh - 210px)}}
  table{{border-collapse:collapse;background:#fff;font-size:12px}}

  /* CABEÇALHO */
  thead{{position:sticky;top:0;z-index:20}}
  tr.tr-header{{background:#1a2332;color:#fff}}
  tr.tr-filter{{background:#0f1927}}

  th.sort-th{{
    padding:0;border-right:1px solid #273449;white-space:nowrap;
    vertical-align:middle;user-select:none;
  }}
  .th-inner{{
    display:flex;align-items:center;justify-content:space-between;
    gap:4px;padding:9px 10px;cursor:pointer;
    font-size:10px;font-weight:500;letter-spacing:.4px;text-transform:uppercase;
  }}
  .th-inner:hover{{background:#273449}}
  .sort-icon{{font-size:10px;opacity:.5;flex-shrink:0}}
  th.sort-th.asc  .sort-icon{{opacity:1;color:#60a5fa}}
  th.sort-th.desc .sort-icon{{opacity:1;color:#60a5fa}}

  /* sticky primeiras colunas */
  th.col-id    {{position:sticky;left:0;  z-index:30;background:#1a2332}}
  th.col-razao {{position:sticky;left:52px;z-index:30;background:#1a2332;min-width:210px}}
  td.col-id    {{position:sticky;left:0;  z-index:5; background:#fff;color:#64748b;font-weight:500;width:52px;min-width:52px}}
  td.col-razao {{position:sticky;left:52px;z-index:5; background:#fff;min-width:210px;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  tbody tr:hover td.col-id,
  tbody tr:hover td.col-razao{{background:#f0f7ff}}

  /* linha de filtro — célula */
  td.tf-cell{{padding:3px 5px;border-right:1px solid #1a2d42}}
  td.tf-cell.col-id    {{position:sticky;left:0;  z-index:15;background:#0f1927}}
  td.tf-cell.col-razao {{position:sticky;left:52px;z-index:15;background:#0f1927}}

  .tf-input{{width:100%;padding:4px 7px;background:#1e2f42;border:1px solid #2d4057;
             border-radius:5px;color:#e2e8f0;font-size:11px;font-family:inherit;outline:none}}
  .tf-input:focus{{border-color:#3b82f6;background:#1a2d42}}
  .tf-input option{{background:#1e2f42;color:#e2e8f0}}

  /* células de dados */
  td{{padding:7px 10px;border-bottom:1px solid #f0f3f7;border-right:1px solid #f5f7fa;
      white-space:nowrap;vertical-align:middle}}
  tr:last-child td{{border-bottom:none}}
  tbody tr:hover{{background:#f0f7ff}}

  /* badges */
  .sim {{background:#dcfce7;color:#16a34a;font-size:10px;font-weight:600;padding:1px 7px;border-radius:8px;display:inline-block}}
  .nao {{background:#f1f5f9;color:#94a3b8;font-size:10px;padding:1px 7px;border-radius:8px;display:inline-block}}
  .ativo-s{{background:#dcfce7;color:#16a34a;font-size:10px;font-weight:600;padding:1px 7px;border-radius:8px;display:inline-block}}
  .ativo-n{{background:#fee2e2;color:#dc2626;font-size:10px;font-weight:600;padding:1px 7px;border-radius:8px;display:inline-block}}
  .vip-tag{{background:#fef3c7;color:#d97706;font-size:10px;font-weight:600;padding:1px 7px;border-radius:8px;display:inline-block}}
</style>
</head>
<body>

<div class="header">
  <h1>🏢 Base Guarani — Clientes</h1>
  <span class="badge" id="badge-total">{n} clientes</span>
</div>

<div class="toolbar">
  <input class="search-box" id="search" type="text"
         placeholder="🔍  Buscar por razão, CNPJ, cidade, vendedor, nome..." oninput="filtrar()">
  <button class="btn" id="btn-filtros" onclick="toggleFiltros()">▽ Filtros por coluna</button>
  <button class="btn" id="btn-cols"    onclick="toggleCols()">⚙ Colunas</button>
  <button class="btn"                  onclick="limparFiltros()">✕ Limpar filtros</button>
</div>

<div class="col-panel" id="col-panel">
  <h3>Exibir / Ocultar Colunas</h3>
  <div class="col-grid" id="col-grid"></div>
</div>

<div class="count" id="count">Carregando...</div>

<div class="table-wrap">
  <table id="tabela">
    <thead>
      <tr class="tr-header" id="tr-header"></tr>
      <tr class="tr-filter" id="tr-filter" style="display:none"></tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>

<script>
const DADOS    = {json_dados};
const COLUNAS  = {json_colunas};
const BOOL_SET = new Set({json_bool});
const DROP_SET = new Set({json_dropdown});
const DEF_VIS  = new Set({json_default});

let visivel  = new Set(DEF_VIS);
let sortCol  = -1, sortAsc = true;
let filtrados = [...DADOS];
let colFiltros = {{}};      // coluna → valor do filtro por coluna
let filtrosAtivos = false;

// ── Utils ────────────────────────────────────────────────────────────────────
function isTrue(v) {{
  const u = (v||"").toString().toUpperCase().trim();
  return u==="SIM"||u==="1"||u==="X";
}}
function isFalse(v) {{
  const u = (v||"").toString().toUpperCase().trim();
  return !u || u==="NÃO"||u==="NAO"||u==="0"||u==="-";
}}

// ── Painel colunas ───────────────────────────────────────────────────────────
function toggleCols() {{
  document.getElementById("col-panel").classList.toggle("open");
  document.getElementById("btn-cols").classList.toggle("on");
}}
function buildColPanel() {{
  const grid = document.getElementById("col-grid");
  COLUNAS.forEach(c => {{
    const lbl = document.createElement("label");
    lbl.className = "col-item";
    const cb = document.createElement("input");
    cb.type = "checkbox"; cb.checked = visivel.has(c);
    cb.onchange = () => {{
      if(cb.checked) visivel.add(c); else visivel.delete(c);
      buildHeader(); buildFilterRow(); renderTabela();
    }};
    lbl.appendChild(cb);
    lbl.appendChild(document.createTextNode(c));
    grid.appendChild(lbl);
  }});
}}

// ── Filtros por coluna ───────────────────────────────────────────────────────
function toggleFiltros() {{
  filtrosAtivos = !filtrosAtivos;
  document.getElementById("tr-filter").style.display = filtrosAtivos ? "" : "none";
  document.getElementById("btn-filtros").classList.toggle("on", filtrosAtivos);
}}
function limparFiltros() {{
  colFiltros = {{}};
  document.getElementById("search").value = "";
  document.querySelectorAll(".tf-input").forEach(el => el.value = "");
  filtrar();
}}

function buildFilterRow() {{
  const tr = document.getElementById("tr-filter");
  tr.innerHTML = "";
  const cols = COLUNAS.filter(c => visivel.has(c));
  cols.forEach(c => {{
    const td = document.createElement("td");
    td.className = "tf-cell" + (c==="ID" ? " col-id" : c==="RAZÃO" ? " col-razao" : "");

    if(BOOL_SET.has(c) || DROP_SET.has(c)) {{
      // Dropdown de valores únicos
      const sel = document.createElement("select");
      sel.className = "tf-input";
      const opt0 = document.createElement("option");
      opt0.value=""; opt0.textContent="Todos"; sel.appendChild(opt0);

      if(BOOL_SET.has(c)) {{
        ["SIM","NÃO"].forEach(v => {{
          const o=document.createElement("option"); o.value=v; o.textContent=v; sel.appendChild(o);
        }});
      }} else {{
        const vals = [...new Set(DADOS.map(d=>(d[c]||"").trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"pt-BR"));
        vals.forEach(v => {{
          const o=document.createElement("option"); o.value=v; o.textContent=v; sel.appendChild(o);
        }});
      }}
      if(colFiltros[c]) sel.value = colFiltros[c];
      sel.onchange = () => {{ colFiltros[c] = sel.value; filtrar(); }};
      td.appendChild(sel);
    }} else {{
      // Input de texto
      const inp = document.createElement("input");
      inp.type="text"; inp.className="tf-input";
      inp.placeholder = c==="ID"?"ID":c==="RAZÃO"?"Razão...":"";
      inp.value = colFiltros[c]||"";
      inp.oninput = () => {{ colFiltros[c] = inp.value.toLowerCase().trim(); filtrar(); }};
      td.appendChild(inp);
    }}
    tr.appendChild(td);
  }});
}}

// ── Cabeçalho ────────────────────────────────────────────────────────────────
function buildHeader() {{
  const tr = document.getElementById("tr-header");
  tr.innerHTML = "";
  const cols = COLUNAS.filter(c => visivel.has(c));
  cols.forEach((c, visIdx) => {{
    const colIdx = COLUNAS.indexOf(c);
    const th = document.createElement("th");
    th.className = "sort-th" + (c==="ID" ? " col-id" : c==="RAZÃO" ? " col-razao" : "");
    if(sortCol===colIdx) th.classList.add(sortAsc?"asc":"desc");
    th.dataset.colidx = colIdx;

    const inner = document.createElement("div");
    inner.className = "th-inner";
    inner.innerHTML = `<span>${{c}}</span><span class="sort-icon">${{
      sortCol===colIdx ? (sortAsc?"▲":"▼") : "↕"
    }}</span>`;
    inner.onclick = () => sort(colIdx);
    th.appendChild(inner);
    tr.appendChild(th);
  }});
}}

// ── Render tabela ────────────────────────────────────────────────────────────
function celula(c, v) {{
  const cls = c==="ID" ? " col-id" : c==="RAZÃO" ? " col-razao" : "";
  let inner = "";

  if(c==="ATIVO")
    inner = isTrue(v) ? '<span class="ativo-s">SIM</span>' : '<span class="ativo-n">NÃO</span>';
  else if(c==="VIP")
    inner = isTrue(v) ? '<span class="vip-tag">VIP</span>' : (v||"");
  else if(BOOL_SET.has(c))
    inner = isTrue(v) ? '<span class="sim">✓</span>' : '<span class="nao">—</span>';
  else
    inner = v ? v.replace(/</g,"&lt;") : "";

  const center = (BOOL_SET.has(c)&&c!=="ATIVO"&&c!=="VIP") ? ' style="text-align:center"' : "";
  const title  = (c==="RAZÃO"||c==="CLIENTE") ? ` title="${{v||""}}"` : "";
  return `<td class="${{cls}}"${{center}}${{title}}>${{inner}}</td>`;
}}

function renderTabela() {{
  const tbody = document.getElementById("tbody");
  const cols  = COLUNAS.filter(c => visivel.has(c));
  if(!filtrados.length) {{
    tbody.innerHTML = `<tr><td colspan="${{cols.length}}" style="text-align:center;padding:32px;color:#94a3b8">Nenhum resultado encontrado.</td></tr>`;
    document.getElementById("count").textContent = "Nenhum resultado.";
    return;
  }}
  tbody.innerHTML = filtrados.map(d =>
    `<tr>${{cols.map(c => celula(c, d[c]||"")).join("")}}</tr>`
  ).join("");
  document.getElementById("count").textContent =
    `Exibindo ${{filtrados.length}} de ${{DADOS.length}} clientes`;
}}

// ── Filtrar ──────────────────────────────────────────────────────────────────
function filtrar() {{
  const q = document.getElementById("search").value.toLowerCase().trim();

  filtrados = DADOS.filter(d => {{
    // busca global
    if(q) {{
      const txt = ["RAZÃO","CLIENTE","CNPJ PRINCIPAL","CIDADE","VENDEDOR",
                   "RESPONSÁVEL","SEGMENTO","NOME SÓCIO","NOME DECISOR",
                   "NOME USUÁRIO CHAVE","EMAIL SÓCIO","E-MAIL DECISOR"]
        .map(k => d[k]||"").join(" ").toLowerCase();
      if(!txt.includes(q)) return false;
    }}
    // filtros por coluna
    for(const [col, fv] of Object.entries(colFiltros)) {{
      if(!fv) continue;
      const dv = (d[col]||"").toString();
      if(BOOL_SET.has(col)) {{
        const ok = isTrue(dv);
        if(fv==="SIM" && !ok)  return false;
        if(fv==="NÃO" && ok)   return false;
      }} else if(DROP_SET.has(col)) {{
        if(dv !== fv) return false;
      }} else {{
        if(!dv.toLowerCase().includes(fv)) return false;
      }}
    }}
    return true;
  }});

  if(sortCol>=0) aplicarSort();
  else renderTabela();
}}

// ── Ordenar ──────────────────────────────────────────────────────────────────
function sort(colIdx) {{
  if(sortCol===colIdx) sortAsc = !sortAsc;
  else {{ sortCol=colIdx; sortAsc=true; }}
  buildHeader();       // atualiza ícones
  aplicarSort();
}}
function aplicarSort() {{
  const key = COLUNAS[sortCol];
  filtrados.sort((a,b) => {{
    const va=(a[key]||"").toString().toLowerCase();
    const vb=(b[key]||"").toString().toLowerCase();
    const na=parseFloat(va), nb=parseFloat(vb);
    const cmp=(!isNaN(na)&&!isNaN(nb))? na-nb : va.localeCompare(vb,"pt-BR");
    return sortAsc?cmp:-cmp;
  }});
  renderTabela();
}}

// ── Init ─────────────────────────────────────────────────────────────────────
buildColPanel();
buildHeader();
buildFilterRow();
filtrar();
</script>
</body>
</html>"""
    return html


if __name__ == "__main__":
    print("Lendo dados do Excel...")
    dados = ler_dados()
    print(f"  >> {len(dados)} registros")
    html = gerar_html(dados)
    saida = BASE / "guarani" / "base" / "base_guarani.html"
    saida.write_text(html, encoding="utf-8")
    print(f"  >> HTML gerado: {saida}")
    print(f"  >> Tamanho: {len(html):,} bytes")
