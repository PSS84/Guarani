import os
import sys
from pathlib import Path

from flask import Flask, render_template

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "guarani" / "templates"
SCRIPT_DIR = BASE_DIR / "guarani" / "Script"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from precos_2026 import carregar_precos_2026  # noqa: E402

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))


@app.route("/")
def home():
    return (
        "DT_Claude online. Acesse "
        "<a href='/guarani/precos'>/guarani/precos</a> para ver a tabela de precos."
    )


@app.route("/guarani/precos")
def pagina_precos():
    planilha = BASE_DIR / "dados" / "TABELA 2026.xlsx"
    erro = None
    secoes = []
    total_itens = 0

    try:
        dados = carregar_precos_2026(planilha)
        secoes = dados["secoes"]
        total_itens = dados["total_itens"]
    except Exception as exc:
        erro = f"Nao foi possivel carregar a planilha: {exc}"

    return render_template(
        "precos_2026.html",
        planilha_relativa="dados/TABELA 2026.xlsx (aba 2026)",
        secoes=secoes,
        total_itens=total_itens,
        erro=erro,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
