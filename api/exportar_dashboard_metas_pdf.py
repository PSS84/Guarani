"""
Exporta o dashboard_metas por vendedor para PDF paisagem A4.

Uso:
  python api/exportar_dashboard_metas_pdf.py           # mes atual
  python api/exportar_dashboard_metas_pdf.py --mes 6  # Junho
  python api/exportar_dashboard_metas_pdf.py --mes 5  # Maio

Saida:
  guarani/vendas/pdf/dashboard_metas_<vendedor>_<mes><ano>_<timestamp>.pdf
"""
import argparse
import io
import re
import time
from datetime import datetime
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

MESES_NOME = {1:"janeiro",2:"fevereiro",3:"marco",4:"abril",5:"maio",6:"junho",
              7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"}

parser = argparse.ArgumentParser()
parser.add_argument("--mes", type=int, default=datetime.today().month,
                    help="Número do mês (1-12). Padrão: mês atual.")
args, _ = parser.parse_known_args()

MES_NUM  = args.mes
MES_SLUG = MESES_NOME.get(MES_NUM, str(MES_NUM))
ANO      = datetime.today().year

BASE_URL = "http://localhost:5000/guarani/vendas/metas"

OUT_DIR = Path(__file__).resolve().parent.parent / "guarani" / "vendas" / "pdf"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VENDEDORES = [
    "Junior Lopes",
    "Rayssa Karapeticov",
    "Paulo Souza",
    "Ronaldo Nascimento",
]

# A4 paisagem a 150 dpi: 297mm x 210mm
DPI       = 150
A4_W_PX   = int(297 / 25.4 * DPI)   # 1754 px
A4_H_PX   = int(210 / 25.4 * DPI)   # 1240 px

TS = datetime.now().strftime("%Y%m%d_%H%M%S")

def nome_arquivo(vendedor: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "_", vendedor.lower().strip()).strip("_")
    return OUT_DIR / f"dashboard_metas_{slug}_{MES_SLUG}{ANO}_{TS}.pdf"


def screenshot_para_pdf(img_bytes: bytes, saida: Path):
    """Converte bytes PNG em PDF A4 paisagem (multi-pagina se necessario)."""
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # Escala para caber na largura do A4 paisagem
    scale  = A4_W_PX / img.width
    img_w  = A4_W_PX
    img_h  = int(img.height * scale)
    img    = img.resize((img_w, img_h), Image.LANCZOS)

    # Fatia em paginas A4
    pages = []
    y = 0
    while y < img_h:
        fatia = img.crop((0, y, img_w, min(y + A4_H_PX, img_h)))
        if fatia.height < A4_H_PX:
            # Preenche o resto com branco
            pagina = Image.new("RGB", (img_w, A4_H_PX), "white")
            pagina.paste(fatia, (0, 0))
        else:
            pagina = fatia
        pages.append(pagina)
        y += A4_H_PX

    # Salva PDF
    if len(pages) == 1:
        pages[0].save(str(saida), "PDF", resolution=DPI)
    else:
        pages[0].save(
            str(saida), "PDF", resolution=DPI,
            save_all=True, append_images=pages[1:]
        )


def exportar():
    print(f"Destino: {OUT_DIR}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,   # 2x para alta resolucao
        )
        page = ctx.new_page()

        print("Abrindo dashboard_metas...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)

        # Aguarda vendedores carregarem no select
        page.wait_for_function(
            "document.querySelector('#vendedorSelect').options.length > 1",
            timeout=15_000,
        )
        time.sleep(0.5)

        for vendedor in VENDEDORES:
            primeiro_nome = vendedor.split()[0]
            print(f"  > {vendedor}...", end=" ", flush=True)

            # 1. Seleciona o vendedor e aguarda o nome aparecer na sidebar
            page.select_option("#vendedorSelect", label=vendedor)

            # Aguarda a sidebar exibir o nome correto (confirma que a API respondeu)
            page.wait_for_function(
                f"""() => {{
                    const el = document.querySelector('#sidebarProfile .profile-name');
                    return el && el.textContent.toLowerCase().includes('{primeiro_nome.lower()}');
                }}""",
                timeout=20_000,
            )

            # 2. Seleciona o mês no filtro
            mes_sel = page.query_selector("#mesSelect")
            if mes_sel and mes_sel.is_visible():
                page.select_option("#mesSelect", value=str(MES_NUM))
                # Aguarda rede estabilizar apos troca de mes
                page.wait_for_load_state("networkidle", timeout=15_000)

            # 3. Aguarda charts animarem completamente
            time.sleep(1.0)

            # 4. Injeta CSS para remover overflow e expandir altura total
            #    -> captura tudo sem cortes
            page.add_style_tag(content="""
                html, body {
                    height: auto !important;
                    overflow: visible !important;
                }
                .content {
                    overflow: visible !important;
                    height: auto !important;
                    min-height: 0 !important;
                }
                .main {
                    overflow: visible !important;
                    height: auto !important;
                    flex: none !important;
                }
                .sidebar {
                    height: auto !important;
                    overflow: visible !important;
                    position: relative !important;
                }
            """)
            time.sleep(0.3)

            # 5. Captura screenshot fiel da pagina inteira
            img_bytes = page.screenshot(full_page=True, type="png")

            # 6. Converte para PDF A4 paisagem
            saida = nome_arquivo(vendedor)
            screenshot_para_pdf(img_bytes, saida)

            # 7. Remove o style tag injetado para o proximo vendedor
            page.evaluate("""
                const tags = document.querySelectorAll('style');
                tags[tags.length - 1].remove();
            """)

            print(f"OK > {saida.name}")

        browser.close()

    print(f"\nOK: {len(VENDEDORES)} PDF(s) gerado(s) em: {OUT_DIR}")


if __name__ == "__main__":
    exportar()
