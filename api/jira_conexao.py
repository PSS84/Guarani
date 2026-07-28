# -*- coding: utf-8 -*-
"""
Módulo de conexão com o Jira Cloud (REST API v3).

Centraliza autenticação e sessão HTTP para ser reutilizado por outros scripts.

Credenciais lidas do .env na raiz do projeto:
    JIRA_URL    = https://suaempresa.atlassian.net
    JIRA_EMAIL  = seu.email@empresa.com
    JIRA_TOKEN  = <API token de id.atlassian.com/manage-profile/security/api-tokens>

── Uso como módulo (em outros scripts) ─────────────────────────────
    from jira_conexao import conectar, api_get

    jira = conectar()                       # valida credenciais e retorna o cliente
    dados = api_get(jira, "/rest/api/3/project/search", {"maxResults": 50})

── Uso direto (linha de comando) ───────────────────────────────────
    python jira_conexao.py          # conecta, confirma o usuário e lista projetos
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


class JiraError(Exception):
    """Erro de conexão/autenticação com o Jira."""


@dataclass
class JiraClient:
    """Cliente autenticado do Jira: sessão HTTP + URL base + usuário logado."""
    base_url: str
    sessao: requests.Session
    usuario: str


def carregar_credenciais():
    """Lê e valida as credenciais do .env. Retorna (url, email, token)."""
    url = os.environ.get("JIRA_URL", "").rstrip("/")
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_TOKEN", "")
    faltando = [n for n, v in [("JIRA_URL", url), ("JIRA_EMAIL", email), ("JIRA_TOKEN", token)] if not v]
    if faltando:
        raise JiraError("Variáveis ausentes no .env: " + ", ".join(faltando))
    return url, email, token


def conectar(timeout: int = 30) -> JiraClient:
    """Cria a sessão autenticada e valida as credenciais via /myself.

    Retorna um JiraClient pronto para uso. Levanta JiraError se falhar.
    """
    url, email, token = carregar_credenciais()

    sessao = requests.Session()
    sessao.auth = HTTPBasicAuth(email, token)
    sessao.headers.update({"Accept": "application/json"})

    resp = sessao.get(f"{url}/rest/api/3/myself", timeout=timeout)
    if resp.status_code == 401:
        raise JiraError("401 — credenciais inválidas (verifique JIRA_EMAIL e JIRA_TOKEN).")
    if resp.status_code != 200:
        raise JiraError(f"{resp.status_code} — falha ao conectar: {resp.text[:200]}")

    usuario = resp.json().get("displayName", "(desconhecido)")
    return JiraClient(base_url=url, sessao=sessao, usuario=usuario)


def api_get(jira: JiraClient, path: str, params: dict | None = None, timeout: int = 30) -> dict:
    """GET genérico em um endpoint da API do Jira. Retorna o JSON como dict.

    `path` deve começar com '/', ex.: '/rest/api/3/project/search'.
    """
    resp = jira.sessao.get(f"{jira.base_url}{path}", params=params or {}, timeout=timeout)
    if resp.status_code != 200:
        raise JiraError(f"{resp.status_code} em {path}: {resp.text[:200]}")
    return resp.json()


def _main() -> None:
    """Execução direta: conecta, confirma o usuário e lista os projetos acessíveis."""
    try:
        jira = conectar()
    except JiraError as e:
        print(f"[ERRO] {e}")
        sys.exit(1)

    print("Conexão com o Jira estabelecida.")
    print(f"  Site:     {jira.base_url}")
    print(f"  Usuário:  {jira.usuario}")

    try:
        dados = api_get(jira, "/rest/api/3/project/search", {"maxResults": 50})
        projetos = dados.get("values", [])
        print(f"  Projetos: {dados.get('total', len(projetos))} acessíveis")
        for p in projetos:
            print(f"    {p.get('key'):<10} {p.get('name')}")
    except JiraError as e:
        print(f"[AVISO] conectado, mas falhou ao listar projetos: {e}")


if __name__ == "__main__":
    _main()
