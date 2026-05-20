"""
Gera guarani/base/base_guarani.html
Lê MapaOportunidadeClientesBaseGuarani.xlsm (sheet Clientes, 213 linhas, 85 colunas)
e embute os dados como JSON no HTML.
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
    for row in rows[1:]:  # pular cabeçalho
        if all(c is None for c in row):
            continue
        rec = {COLUNAS[i]: val(row[i]) for i in range(min(len(COLUNAS), len(row)))}
        dados.append(rec)
    return dados


def gerar_html(dados):
    n = len(dados)
    json_dados = json.dumps(dados, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Base Guarani — Clientes</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Inter',sans-serif;background:#f4f6f9;color:#1a2332;padding:24px}}

  /* HEADER */
  .header{{background:#1a2332;color:#fff;padding:20px 28px;border-radius:10px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center}}
  .header h1{{font-size:18px;font-weight:600;letter-spacing:.3px}}
  .badge{{background:#3b82f6;color:#fff;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:500}}

  /* CONTROLS */
  .controls{{display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap}}
  input[type=text]{{flex:1;min-width:200px;padding:10px 14px;border:1px solid #dde3ec;border-radius:8px;font-size:13px;font-family:inherit;outline:none;transition:border .2s}}
  input[type=text]:focus{{border-color:#3b82f6}}
  select{{padding:10px 14px;border:1px solid #dde3ec;border-radius:8px;font-size:13px;font-family:inherit;outline:none;background:#fff;cursor:pointer}}
  select:focus{{border-color:#3b82f6}}

  .count{{font-size:12px;color:#64748b;padding:10px 0;margin-bottom:4px}}

  /* TABLE */
  .table-wrap{{overflow-x:auto;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.07)}}
  table{{width:100%;border-collapse:collapse;background:#fff}}
  thead tr{{background:#1a2332;color:#fff}}
  th{{padding:11px 14px;text-align:left;font-size:11px;font-weight:500;letter-spacing:.5px;text-transform:uppercase;cursor:pointer;user-select:none;white-space:nowrap}}
  th:hover{{background:#273449}}
  th.asc::after{{content:' ▲';font-size:10px}}
  th.desc::after{{content:' ▼';font-size:10px}}
  td{{padding:9px 14px;font-size:12px;border-bottom:1px solid #f0f3f7;white-space:nowrap}}
  tr:last-child td{{border-bottom:none}}
  tbody tr:hover{{background:#f0f7ff;cursor:pointer}}
  .hidden{{display:none}}

  /* BADGES SIM/NÃO */
  .sim{{display:inline-block;background:#dcfce7;color:#16a34a;font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px}}
  .nao{{display:inline-block;background:#fee2e2;color:#dc2626;font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px}}
  .vip{{display:inline-block;background:#fef3c7;color:#d97706;font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px}}

  .id-col{{color:#64748b;font-weight:500;width:50px}}
  .cnpj-col{{font-family:monospace;font-size:11px;color:#475569}}
  .razao-col{{min-width:220px;white-space:normal!important;line-height:1.3}}

  /* MODAL */
  .overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;justify-content:center;align-items:flex-start;padding:40px 20px;overflow-y:auto}}
  .overlay.open{{display:flex}}
  .modal{{background:#fff;border-radius:12px;width:100%;max-width:900px;box-shadow:0 8px 32px rgba(0,0,0,.2);overflow:hidden}}
  .modal-head{{background:#1a2332;color:#fff;padding:18px 24px;display:flex;justify-content:space-between;align-items:center}}
  .modal-head h2{{font-size:15px;font-weight:600}}
  .close-btn{{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;line-height:1;padding:0 4px}}
  .close-btn:hover{{color:#3b82f6}}
  .modal-body{{padding:20px 24px;max-height:75vh;overflow-y:auto}}

  /* SEÇÕES DO MODAL */
  .sec{{margin-bottom:20px}}
  .sec-title{{font-size:11px;font-weight:600;letter-spacing:.6px;text-transform:uppercase;color:#3b82f6;margin-bottom:10px;padding-bottom:4px;border-bottom:1px solid #e2e8f0}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}}
  .field{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 10px}}
  .field-label{{font-size:10px;color:#64748b;font-weight:500;text-transform:uppercase;letter-spacing:.3px;margin-bottom:3px}}
  .field-val{{font-size:12px;color:#1a2332;font-weight:500;word-break:break-word;white-space:normal}}
  .field-val.sim-v{{color:#16a34a;font-weight:600}}
  .field-val.nao-v{{color:#dc2626}}
  .field-val.empty{{color:#94a3b8;font-style:italic}}

  /* CNPJS extras */
  .cnpj-list{{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}}
  .cnpj-tag{{font-family:monospace;font-size:11px;background:#e2e8f0;color:#1a2332;padding:2px 8px;border-radius:4px}}
</style>
</head>
<body>

<div class="header">
  <h1>🏢 Base Guarani — Clientes</h1>
  <span class="badge" id="total">{n} clientes</span>
</div>

<div class="controls">
  <input type="text" id="search" placeholder="Pesquisar por razão social, CNPJ, cidade, vendedor..." oninput="filtrar()">
  <select id="filtro-ativo" onchange="filtrar()">
    <option value="">Todos (Ativo)</option>
    <option value="SIM">Ativos</option>
    <option value="NÃO">Inativos</option>
  </select>
  <select id="filtro-uf" onchange="filtrar()">
    <option value="">Todos (UF)</option>
  </select>
  <select id="filtro-vendedor" onchange="filtrar()">
    <option value="">Todos (Vendedor)</option>
  </select>
</div>

<div class="count" id="count">Carregando...</div>

<div class="table-wrap">
<table>
  <thead>
    <tr>
      <th onclick="sort(0)">ID</th>
      <th onclick="sort(1)">Razão Social</th>
      <th onclick="sort(2)">CNPJ Principal</th>
      <th onclick="sort(3)">Cidade</th>
      <th onclick="sort(4)">UF</th>
      <th onclick="sort(5)">Vendedor</th>
      <th onclick="sort(6)">Responsável</th>
      <th onclick="sort(7)">Ativo</th>
      <th onclick="sort(8)">ERP</th>
      <th onclick="sort(9)">AFV</th>
      <th onclick="sort(10)">BI</th>
      <th onclick="sort(11)">B2B</th>
      <th onclick="sort(12)">CLOUD</th>
      <th onclick="sort(13)">Qtde Usr ERP</th>
      <th onclick="sort(14)">VIP</th>
      <th onclick="sort(15)">Segmento</th>
    </tr>
  </thead>
  <tbody id="tbody"></tbody>
</table>
</div>

<!-- MODAL -->
<div class="overlay" id="overlay" onclick="fecharModal(event)">
  <div class="modal" id="modal">
    <div class="modal-head">
      <h2 id="modal-title">Detalhes do Cliente</h2>
      <button class="close-btn" onclick="fecharModal()">✕</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>

<script>
const DADOS = {json_dados};

const COLS_TABLE = [
  "ID","RAZÃO","CNPJ PRINCIPAL","CIDADE","UF","VENDEDOR","RESPONSÁVEL",
  "ATIVO","MÓDULO GUARANI ERP","MÓDULO GUARANI AFV","MÓDULO GUARANI BI",
  "MÓDULO GUARANI B2B","MÓDULO GUARANI CLOUD","QTDE USUÁRIO ERP","VIP","SEGMENTO"
];

// Seções para o modal
const SECOES = [
  {{
    titulo: "Identificação",
    campos: ["QTDE","ID","IMPLANTADO","CONTRATANTE","RAZÃO","CLIENTE","VIP","VENDEDOR","RESPONSÁVEL","DATA ASSINATURA CONTRATO","ATIVO","SEGMENTO","RAMO ATIVIDADE","BÔNUS","COUNT"]
  }},
  {{
    titulo: "Localização",
    campos: ["CIDADE","UF","LOGRADOURO","BAIRRO","CEP"]
  }},
  {{
    titulo: "CNPJs",
    campos: ["CNPJ PRINCIPAL","CNPJ 1","CNPJ 2","CNPJ 3","CNPJ 4","CNPJ 5","CNPJ 6","CNPJ 7","CNPJ 8","CNPJ 9","CNPJ 10","CNPJ 11","CNPJ 12","CNPJ 13"]
  }},
  {{
    titulo: "Contato — Sócio",
    campos: ["NOME SÓCIO","EMAIL SÓCIO","WHATSAPP SÓCIO"]
  }},
  {{
    titulo: "Contato — Decisor",
    campos: ["NOME DECISOR","E-MAIL DECISOR","WHATSAPP DECISOR"]
  }},
  {{
    titulo: "Contato — Usuário Chave",
    campos: ["NOME USUÁRIO CHAVE","E-MAIL USUÁRIO CHAVE","WHATSAPP USUÁRIO CHAVE"]
  }},
  {{
    titulo: "Módulos Principais",
    campos: ["MÓDULO GUARANI ERP","MÓDULO GUARANI AFV","MÓDULO GUARANI BI","MÓDULO GUARANI B2B","MÓDULO GUARANI CLOUD"]
  }},
  {{
    titulo: "Add-ons ERP",
    campos: ["ADDON ERP PCP","ADDON ERP WMS","ADDON ERP MDFE","ADDON ERP TELEMARKETING","ADDON ERP CONTÁBIL","ADDON ERP CIAP","ADDON ERP MDE","ADDON ERP IMPORTAÇÃO XML","ADDON ERP LINK PAGAMENTO","ADDON ERP BOLETO WHATSAPP","ADDON ERP CTE"]
  }},
  {{
    titulo: "Alianças ERP",
    campos: ["ALIANÇA ERP CONCIL","ALIANÇA ERP ROUTEASY","ALIANÇA ERP PDV","ALIANÇA ERP PLUGGTO","ALIANÇA ERP TRAY","ALIANÇA ERP KONCILI","ALIANÇA ERP JETCOMMERCE"]
  }},
  {{
    titulo: "Add-ons AFV",
    campos: ["ADDON AFV PESQUISA MERCADO","ADDON AFV ORÇAMENTO WEB","ADDON AFV AGENDA","ADDON AFV IARA","ADDON AFV MULTILOJAS","ADDON AFV LOJA B2B","ADDON AFV PROPOSTA WEB"]
  }},
  {{
    titulo: "PDV",
    campos: ["GUARANI PDV MARKET"]
  }},
  {{
    titulo: "Quantidades",
    campos: ["QTDE USUÁRIO ERP","QTDE GUARANI B2B","QTDE GUARANI BI","QTDE USUÁRIO AFV","QTDE USUÁRIO AFV PREPOSTO","QTDE USUÁRIO WMS","QTDE USUÁRIO PDV","QTDE USUÁRIO TELEMARKETING","TS CLOUD","QTDE USUÁRIO CONTÁBIL"]
  }},
  {{
    titulo: "Online",
    campos: ["SITE/REDES SOCIAIS"]
  }}
];

const SIM_NOMES = new Set([
  "MÓDULO GUARANI ERP","MÓDULO GUARANI AFV","MÓDULO GUARANI BI","MÓDULO GUARANI B2B","MÓDULO GUARANI CLOUD",
  "ADDON ERP PCP","ADDON ERP WMS","ADDON ERP MDFE","ADDON ERP TELEMARKETING","ADDON ERP CONTÁBIL",
  "ADDON ERP CIAP","ADDON ERP MDE","ADDON ERP IMPORTAÇÃO XML","ADDON ERP LINK PAGAMENTO",
  "ADDON ERP BOLETO WHATSAPP","ADDON ERP CTE",
  "ALIANÇA ERP CONCIL","ALIANÇA ERP ROUTEASY","ALIANÇA ERP PDV","ALIANÇA ERP PLUGGTO",
  "ALIANÇA ERP TRAY","ALIANÇA ERP KONCILI","ALIANÇA ERP JETCOMMERCE",
  "ADDON AFV PESQUISA MERCADO","ADDON AFV ORÇAMENTO WEB","ADDON AFV AGENDA","ADDON AFV IARA",
  "ADDON AFV MULTILOJAS","ADDON AFV LOJA B2B","ADDON AFV PROPOSTA WEB",
  "GUARANI PDV MARKET","ATIVO","IMPLANTADO","VIP"
]);

let sortCol = -1, sortAsc = true;
let filtrados = [...DADOS];

// Popular selects
function popularSelects() {{
  const ufs = [...new Set(DADOS.map(d=>d["UF"]).filter(Boolean))].sort();
  const sel_uf = document.getElementById("filtro-uf");
  ufs.forEach(u => {{ const o=document.createElement("option"); o.value=u; o.textContent=u; sel_uf.appendChild(o); }});

  const vends = [...new Set(DADOS.map(d=>d["VENDEDOR"]).filter(Boolean))].sort();
  const sel_v = document.getElementById("filtro-vendedor");
  vends.forEach(v => {{ const o=document.createElement("option"); o.value=v; o.textContent=v; sel_v.appendChild(o); }});
}}

function simNao(v) {{
  if(!v) return '<span class="nao">NÃO</span>';
  const u = v.toString().toUpperCase().trim();
  if(u==="SIM"||u==="1"||u==="X") return '<span class="sim">SIM</span>';
  if(u==="NÃO"||u==="NAO"||u==="0"||u===""||u==="-") return '<span class="nao">NÃO</span>';
  return `<span class="sim">{{v}}</span>`;
}}

function renderTabela() {{
  const tbody = document.getElementById("tbody");
  if(!filtrados.length){{
    tbody.innerHTML = '<tr><td colspan="16" style="text-align:center;padding:30px;color:#94a3b8">Nenhum resultado encontrado.</td></tr>';
    document.getElementById("count").textContent = "Nenhum resultado.";
    return;
  }}
  const linhas = filtrados.map((d,i) => {{
    const ativo = d["ATIVO"]||"";
    const aU = ativo.toUpperCase().trim();
    const ativoHtml = (aU==="SIM"||aU==="1"||aU==="X") ? '<span class="sim">SIM</span>' : '<span class="nao">NÃO</span>';
    const vip = d["VIP"]||"";
    const vipHtml = vip && (vip.toUpperCase().trim()==="SIM"||vip==="1"||vip==="X") ? '<span class="vip">VIP</span>' : (vip||"—");

    const modBadge = k => {{
      const v=(d[k]||"").toUpperCase().trim();
      return (v==="SIM"||v==="1"||v==="X") ? '<span class="sim">✓</span>' : '<span class="nao">—</span>';
    }};

    return `<tr onclick="abrirModal(${{i}})">
      <td class="id-col">${{d["ID"]||""}}</td>
      <td class="razao-col">${{d["RAZÃO"]||d["CLIENTE"]||"—"}}</td>
      <td class="cnpj-col">${{d["CNPJ PRINCIPAL"]||""}}</td>
      <td>${{d["CIDADE"]||""}}</td>
      <td>${{d["UF"]||""}}</td>
      <td>${{d["VENDEDOR"]||""}}</td>
      <td>${{d["RESPONSÁVEL"]||""}}</td>
      <td>${{ativoHtml}}</td>
      <td style="text-align:center">${{modBadge("MÓDULO GUARANI ERP")}}</td>
      <td style="text-align:center">${{modBadge("MÓDULO GUARANI AFV")}}</td>
      <td style="text-align:center">${{modBadge("MÓDULO GUARANI BI")}}</td>
      <td style="text-align:center">${{modBadge("MÓDULO GUARANI B2B")}}</td>
      <td style="text-align:center">${{modBadge("MÓDULO GUARANI CLOUD")}}</td>
      <td style="text-align:center">${{d["QTDE USUÁRIO ERP"]||""}}</td>
      <td>${{vipHtml}}</td>
      <td>${{d["SEGMENTO"]||""}}</td>
    </tr>`;
  }}).join("");
  tbody.innerHTML = linhas;
  const total = DADOS.length;
  document.getElementById("count").textContent = `Exibindo ${{filtrados.length}} de ${{total}} clientes`;
}}

function filtrar() {{
  const q = document.getElementById("search").value.toLowerCase().trim();
  const ativo = document.getElementById("filtro-ativo").value.toUpperCase().trim();
  const uf = document.getElementById("filtro-uf").value;
  const vend = document.getElementById("filtro-vendedor").value;

  filtrados = DADOS.filter(d => {{
    if(q) {{
      const texto = [d["RAZÃO"],d["CLIENTE"],d["CNPJ PRINCIPAL"],d["CIDADE"],d["VENDEDOR"],d["RESPONSÁVEL"],d["SEGMENTO"]].join(" ").toLowerCase();
      if(!texto.includes(q)) return false;
    }}
    if(ativo) {{
      const a=(d["ATIVO"]||"").toUpperCase().trim();
      const eAtivo=(a==="SIM"||a==="1"||a==="X");
      if(ativo==="SIM" && !eAtivo) return false;
      if(ativo==="NÃO" && eAtivo) return false;
    }}
    if(uf && d["UF"]!==uf) return false;
    if(vend && d["VENDEDOR"]!==vend) return false;
    return true;
  }});

  if(sortCol>=0) aplicarSort();
  else renderTabela();
}}

function sort(col) {{
  const ths = document.querySelectorAll("th");
  ths.forEach((t,i)=>{{t.classList.remove("asc","desc")}});
  if(sortCol===col) sortAsc=!sortAsc;
  else {{ sortCol=col; sortAsc=true; }}
  ths[col].classList.add(sortAsc?"asc":"desc");
  aplicarSort();
}}

const SORT_KEYS = ["ID","RAZÃO","CNPJ PRINCIPAL","CIDADE","UF","VENDEDOR","RESPONSÁVEL","ATIVO",
  "MÓDULO GUARANI ERP","MÓDULO GUARANI AFV","MÓDULO GUARANI BI","MÓDULO GUARANI B2B","MÓDULO GUARANI CLOUD",
  "QTDE USUÁRIO ERP","VIP","SEGMENTO"];

function aplicarSort() {{
  const key = SORT_KEYS[sortCol];
  filtrados.sort((a,b) => {{
    const va = (a[key]||"").toString().toLowerCase();
    const vb = (b[key]||"").toString().toLowerCase();
    const na=parseFloat(va), nb=parseFloat(vb);
    const cmp = (!isNaN(na)&&!isNaN(nb)) ? na-nb : va.localeCompare(vb,"pt-BR");
    return sortAsc ? cmp : -cmp;
  }});
  renderTabela();
}}

function abrirModal(idx) {{
  const d = filtrados[idx];
  const razao = d["RAZÃO"]||d["CLIENTE"]||"Cliente";
  document.getElementById("modal-title").textContent = razao;

  let html = "";
  SECOES.forEach(sec => {{
    const temDados = sec.campos.some(c => d[c] && d[c].toString().trim()!=="");
    if(!temDados) return;

    if(sec.titulo==="CNPJs") {{
      const cnpjs = sec.campos.map(c=>d[c]).filter(v=>v&&v.trim());
      if(!cnpjs.length) return;
      html += `<div class="sec"><div class="sec-title">${{sec.titulo}}</div><div class="cnpj-list">`;
      cnpjs.forEach(cn => {{ html += `<span class="cnpj-tag">${{cn}}</span>`; }});
      html += `</div></div>`;
      return;
    }}

    html += `<div class="sec"><div class="sec-title">${{sec.titulo}}</div><div class="grid">`;
    sec.campos.forEach(campo => {{
      const v = (d[campo]||"").toString().trim();
      let valHtml;
      if(SIM_NOMES.has(campo)) {{
        const u=v.toUpperCase();
        if(u==="SIM"||u==="1"||u==="X") valHtml=`<span class="field-val sim-v">✓ SIM</span>`;
        else if(!v||u==="NÃO"||u==="NAO"||u==="-"||u==="0") valHtml=`<span class="field-val nao-v">— NÃO</span>`;
        else valHtml=`<span class="field-val">${{v}}</span>`;
      }} else {{
        valHtml = v ? `<span class="field-val">${{v}}</span>` : `<span class="field-val empty">—</span>`;
      }}
      html += `<div class="field"><div class="field-label">${{campo}}</div>${{valHtml}}</div>`;
    }});
    html += `</div></div>`;
  }});

  document.getElementById("modal-body").innerHTML = html;
  document.getElementById("overlay").classList.add("open");
}}

function fecharModal(e) {{
  if(!e || e.target===document.getElementById("overlay") || e.currentTarget===document.querySelector(".close-btn")) {{
    document.getElementById("overlay").classList.remove("open");
  }}
}}

document.addEventListener("keydown", e => {{ if(e.key==="Escape") document.getElementById("overlay").classList.remove("open"); }});

// INIT
popularSelects();
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
