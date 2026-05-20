"""
Gera guarani/base/base_guarani.html
Lê MapaOportunidadeClientesBaseGuarani.xlsm (sheet Clientes, 214 linhas, 85 colunas)
e embute os dados como JSON no HTML com TODOS os campos visíveis na tabela.
"""

import json
import openpyxl
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Mapeamento correto de índice → nome da coluna
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

# Colunas booleanas (SIM/NÃO)
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

# Colunas CNPJ extras (ocultas por padrão mas presentes nos dados)
CNPJ_EXTRAS = ["CNPJ 1","CNPJ 2","CNPJ 3","CNPJ 4","CNPJ 5","CNPJ 6",
               "CNPJ 7","CNPJ 8","CNPJ 9","CNPJ 10","CNPJ 11","CNPJ 12","CNPJ 13"]


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
    json_dados  = json.dumps(dados,    ensure_ascii=False)
    json_colunas = json.dumps(COLUNAS, ensure_ascii=False)
    json_bool   = json.dumps(list(BOOL_COLS), ensure_ascii=False)
    json_cnpj   = json.dumps(CNPJ_EXTRAS,    ensure_ascii=False)

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

  .header{{background:#1a2332;color:#fff;padding:18px 24px;border-radius:10px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}}
  .header h1{{font-size:17px;font-weight:600;letter-spacing:.3px}}
  .badge{{background:#3b82f6;color:#fff;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:500;white-space:nowrap}}

  .controls{{display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;align-items:center}}
  input[type=text]{{flex:1;min-width:180px;padding:9px 13px;border:1px solid #dde3ec;border-radius:8px;font-size:13px;font-family:inherit;outline:none;transition:border .2s}}
  input[type=text]:focus{{border-color:#3b82f6}}
  select{{padding:9px 12px;border:1px solid #dde3ec;border-radius:8px;font-size:12px;font-family:inherit;outline:none;background:#fff;cursor:pointer}}
  select:focus{{border-color:#3b82f6}}
  .btn{{padding:9px 14px;border:1px solid #dde3ec;border-radius:8px;font-size:12px;font-family:inherit;background:#fff;cursor:pointer;color:#1a2332;white-space:nowrap}}
  .btn:hover{{background:#f0f7ff;border-color:#3b82f6;color:#3b82f6}}
  .btn.active{{background:#3b82f6;color:#fff;border-color:#3b82f6}}

  .count{{font-size:12px;color:#64748b;margin-bottom:8px}}

  .table-wrap{{overflow:auto;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.08);max-height:calc(100vh - 200px)}}
  table{{border-collapse:collapse;background:#fff;font-size:12px;white-space:nowrap}}
  thead tr{{background:#1a2332;color:#fff;position:sticky;top:0;z-index:10}}
  th{{padding:10px 12px;text-align:left;font-size:10px;font-weight:500;letter-spacing:.5px;text-transform:uppercase;cursor:pointer;user-select:none;border-right:1px solid #273449}}
  th:hover{{background:#273449}}
  th.asc::after{{content:' ▲';font-size:9px;opacity:.8}}
  th.desc::after{{content:' ▼';font-size:9px;opacity:.8}}
  th.frozen{{position:sticky;left:0;z-index:20;background:#1a2332}}
  th.frozen2{{position:sticky;left:52px;z-index:20;background:#1a2332;min-width:220px}}

  td{{padding:8px 12px;border-bottom:1px solid #f0f3f7;border-right:1px solid #f5f7fa;vertical-align:middle}}
  tr:last-child td{{border-bottom:none}}
  tbody tr:hover{{background:#f0f7ff}}

  td.frozen{{position:sticky;left:0;background:#fff;z-index:5;color:#64748b;font-weight:500;width:52px;min-width:52px}}
  td.frozen2{{position:sticky;left:52px;background:#fff;z-index:5;min-width:220px;max-width:260px;overflow:hidden;text-overflow:ellipsis}}
  tbody tr:hover td.frozen,
  tbody tr:hover td.frozen2{{background:#f0f7ff}}

  .sim{{display:inline-block;background:#dcfce7;color:#16a34a;font-size:10px;font-weight:600;padding:1px 6px;border-radius:8px}}
  .nao{{display:inline-block;background:#f1f5f9;color:#94a3b8;font-size:10px;padding:1px 6px;border-radius:8px}}
  .vip-tag{{display:inline-block;background:#fef3c7;color:#d97706;font-size:10px;font-weight:600;padding:1px 6px;border-radius:8px}}
  .ativo-sim{{display:inline-block;background:#dcfce7;color:#16a34a;font-size:10px;font-weight:600;padding:1px 6px;border-radius:8px}}
  .ativo-nao{{display:inline-block;background:#fee2e2;color:#dc2626;font-size:10px;font-weight:600;padding:1px 6px;border-radius:8px}}

  .hidden-col{{display:none}}

  /* painel de colunas */
  .col-panel{{display:none;background:#fff;border:1px solid #dde3ec;border-radius:10px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
  .col-panel.open{{display:block}}
  .col-panel h3{{font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}}
  .col-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:6px}}
  .col-item{{display:flex;align-items:center;gap:6px;font-size:12px;cursor:pointer;padding:3px 0}}
  .col-item input{{cursor:pointer;accent-color:#3b82f6}}
</style>
</head>
<body>

<div class="header">
  <h1>🏢 Base Guarani — Clientes</h1>
  <span class="badge" id="total">{n} clientes</span>
</div>

<div class="controls">
  <input type="text" id="search" placeholder="Pesquisar por razão, CNPJ, cidade, vendedor..." oninput="filtrar()">
  <select id="f-ativo" onchange="filtrar()">
    <option value="">Todos (Ativo)</option>
    <option value="SIM">Ativos</option>
    <option value="NAO">Inativos</option>
  </select>
  <select id="f-uf" onchange="filtrar()">
    <option value="">Todos (UF)</option>
  </select>
  <select id="f-vend" onchange="filtrar()">
    <option value="">Todos (Vendedor)</option>
  </select>
  <button class="btn" id="btn-cols" onclick="toggleCols()">⚙ Colunas</button>
</div>

<div class="col-panel" id="col-panel">
  <h3>Exibir / Ocultar Colunas</h3>
  <div class="col-grid" id="col-grid"></div>
</div>

<div class="count" id="count">Carregando...</div>

<div class="table-wrap">
  <table id="tabela">
    <thead><tr id="thead-row"></tr></thead>
    <tbody id="tbody"></tbody>
  </table>
</div>

<script>
const DADOS   = {json_dados};
const COLUNAS = {json_colunas};
const BOOL_COLS = new Set({json_bool});
const CNPJ_EXTRAS = new Set({json_cnpj});

// Colunas visíveis por padrão (as mais relevantes)
const DEFAULT_VIS = new Set([
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
  "CONTRATANTE","CLIENTE","LOGRADOURO","BAIRRO","CEP"
]);

let visivel = new Set(DEFAULT_VIS);
let sortCol = -1, sortAsc = true;
let filtrados = [...DADOS];

// ── Selects ───────────────────────────────────────────────────────────────────
function popularSelects() {{
  const ufs  = [...new Set(DADOS.map(d=>d["UF"]).filter(Boolean))].sort();
  const vends = [...new Set(DADOS.map(d=>d["VENDEDOR"]).filter(Boolean))].sort();
  const su = document.getElementById("f-uf");
  const sv = document.getElementById("f-vend");
  ufs.forEach(u  => {{ const o=document.createElement("option"); o.value=u; o.textContent=u; su.appendChild(o); }});
  vends.forEach(v => {{ const o=document.createElement("option"); o.value=v; o.textContent=v; sv.appendChild(o); }});
}}

// ── Painel de colunas ─────────────────────────────────────────────────────────
function toggleCols() {{
  const p = document.getElementById("col-panel");
  const b = document.getElementById("btn-cols");
  p.classList.toggle("open");
  b.classList.toggle("active");
}}

function buildColPanel() {{
  const grid = document.getElementById("col-grid");
  grid.innerHTML = "";
  COLUNAS.forEach(c => {{
    const lbl = document.createElement("label");
    lbl.className = "col-item";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = visivel.has(c);
    cb.onchange = () => {{
      if(cb.checked) visivel.add(c); else visivel.delete(c);
      renderHeader();
      renderTabela();
    }};
    lbl.appendChild(cb);
    lbl.appendChild(document.createTextNode(c));
    grid.appendChild(lbl);
  }});
}}

// ── Render cabeçalho ─────────────────────────────────────────────────────────
function renderHeader() {{
  const tr = document.getElementById("thead-row");
  tr.innerHTML = "";
  COLUNAS.forEach((c, i) => {{
    if(!visivel.has(c)) return;
    const th = document.createElement("th");
    th.textContent = c;
    if(c === "ID")   th.className = "frozen";
    if(c === "RAZÃO") th.className = "frozen2";
    th.onclick = () => sort(i);
    tr.appendChild(th);
  }});
  // Atualizar indicador de sort
  atualizarSortIndicador();
}}

function atualizarSortIndicador() {{
  document.querySelectorAll("th").forEach(th => th.classList.remove("asc","desc"));
  if(sortCol < 0) return;
  const col = COLUNAS[sortCol];
  const ths = [...document.querySelectorAll("#thead-row th")];
  const nomes = [...document.querySelectorAll("#thead-row th")].map(t=>t.textContent.replace(/[ ▲▼]/g,''));
  const idx = nomes.indexOf(col);
  if(idx>=0) ths[idx].classList.add(sortAsc?"asc":"desc");
}}

// ── Render tabela ─────────────────────────────────────────────────────────────
function celula(col, val) {{
  if(col === "ID")    return `<td class="frozen">${{val||""}}</td>`;
  if(col === "RAZÃO") return `<td class="frozen2" title="${{val||""}}">${{val||""}}</td>`;

  if(col === "ATIVO") {{
    const u = (val||"").toUpperCase().trim();
    const ok = u==="SIM"||u==="1"||u==="X";
    return `<td>${{ok?'<span class="ativo-sim">SIM</span>':'<span class="ativo-nao">NÃO</span>'}}</td>`;
  }}
  if(col === "VIP") {{
    const u = (val||"").toUpperCase().trim();
    const ok = u==="SIM"||u==="1"||u==="X";
    return `<td>${{ok?'<span class="vip-tag">VIP</span>':val||""}}</td>`;
  }}
  if(BOOL_COLS.has(col)) {{
    const u = (val||"").toUpperCase().trim();
    const ok = u==="SIM"||u==="1"||u==="X";
    return `<td style="text-align:center">${{ok?'<span class="sim">✓</span>':'<span class="nao">—</span>'}}</td>`;
  }}
  return `<td>${{val||""}}</td>`;
}}

function renderTabela() {{
  const tbody = document.getElementById("tbody");
  if(!filtrados.length) {{
    tbody.innerHTML = '<tr><td colspan="99" style="text-align:center;padding:30px;color:#94a3b8">Nenhum resultado.</td></tr>';
    document.getElementById("count").textContent = "Nenhum resultado.";
    return;
  }}
  const cols = COLUNAS.filter(c => visivel.has(c));
  tbody.innerHTML = filtrados.map(d =>
    `<tr>${{cols.map(c => celula(c, d[c]||"")).join("")}}</tr>`
  ).join("");
  document.getElementById("count").textContent =
    `Exibindo ${{filtrados.length}} de ${{DADOS.length}} clientes`;
}}

// ── Filtrar ───────────────────────────────────────────────────────────────────
function filtrar() {{
  const q    = document.getElementById("search").value.toLowerCase().trim();
  const fAtivo = document.getElementById("f-ativo").value;
  const fUf    = document.getElementById("f-uf").value;
  const fVend  = document.getElementById("f-vend").value;

  filtrados = DADOS.filter(d => {{
    if(q) {{
      const txt = [d["RAZÃO"],d["CLIENTE"],d["CNPJ PRINCIPAL"],d["CIDADE"],
                   d["VENDEDOR"],d["RESPONSÁVEL"],d["SEGMENTO"],d["NOME SÓCIO"],
                   d["NOME DECISOR"],d["NOME USUÁRIO CHAVE"]].join(" ").toLowerCase();
      if(!txt.includes(q)) return false;
    }}
    if(fAtivo) {{
      const a = (d["ATIVO"]||"").toUpperCase().trim();
      const ok = a==="SIM"||a==="1"||a==="X";
      if(fAtivo==="SIM" && !ok) return false;
      if(fAtivo==="NAO" && ok)  return false;
    }}
    if(fUf   && d["UF"]      !== fUf)   return false;
    if(fVend && d["VENDEDOR"] !== fVend) return false;
    return true;
  }});

  if(sortCol >= 0) aplicarSort();
  else renderTabela();
}}

// ── Ordenar ───────────────────────────────────────────────────────────────────
function sort(colIdx) {{
  if(sortCol === colIdx) sortAsc = !sortAsc;
  else {{ sortCol = colIdx; sortAsc = true; }}
  aplicarSort();
  atualizarSortIndicador();
}}

function aplicarSort() {{
  const key = COLUNAS[sortCol];
  filtrados.sort((a,b) => {{
    const va = (a[key]||"").toString().toLowerCase();
    const vb = (b[key]||"").toString().toLowerCase();
    const na = parseFloat(va), nb = parseFloat(vb);
    const cmp = (!isNaN(na)&&!isNaN(nb)) ? na-nb : va.localeCompare(vb,"pt-BR");
    return sortAsc ? cmp : -cmp;
  }});
  renderTabela();
}}

// ── Init ──────────────────────────────────────────────────────────────────────
popularSelects();
buildColPanel();
renderHeader();
filtrar();
</script>
</body>
</html>"""
    return html


if __name__ == "__main__":
    print("Lendo dados do Excel...")
    dados = ler_dados()
    print(f"  >> {len(dados)} registros carregados")
    html = gerar_html(dados)
    saida = BASE / "guarani" / "base" / "base_guarani.html"
    saida.write_text(html, encoding="utf-8")
    print(f"  >> HTML gerado: {saida}")
    print(f"  >> Tamanho: {len(html):,} bytes")
