#!/usr/bin/env python3
# ruff: noqa: E501
"""Write docs/EXEMPLES_REQUETES.md: one correct JSON request per tool, run against the real server.

Each example comes from docs/APPLY.json (the first success case of each tool). It is executed here
before it is written, so the file only holds requests the server accepts. The JSON shown is the whole
`arguments` object: it is what to paste into the Inspector's « Edit as JSON » editor.

Usage: build_examples_md.py [--out docs/EXEMPLES_REQUETES.md]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
ORDER = (
    "health_check",
    "get_qaloun_passage",
    "resolve_source_mapping",
    "list_tajwid_rules",
    "get_tajwid_rule",
    "analyze_qaloun_tajwid",
    "summarize_tajwid",
    "analyze_app_page",
    "list_reading_combinations",
    "get_letter_properties",
    "get_source_page",
    "search_source_pages",
)
ROLE = {
    "health_check": "État du serveur (aucun argument).",
    "get_qaloun_passage": "Texte Qaloun inchangé d'un passage, avec SHA-256 et pages (sur 559).",
    "resolve_source_mapping": "Où tombe le passage dans la numérotation Kufi/Hafs.",
    "list_tajwid_rules": "Liste des règles (filtre facultatif `family`).",
    "get_tajwid_rule": "Une fiche de règle avec ses citations.",
    "analyze_qaloun_tajwid": "Annotations candidates sur 1 à 100 ayat.",
    "summarize_tajwid": "Comptes par règle et par ayah.",
    "analyze_app_page": "Annotations des ayat qui commencent sur une page (1 à 559).",
    "list_reading_combinations": "Lectures permises ensemble dans un ayah.",
    "get_letter_properties": "Makhraj et caractéristiques d'une lettre.",
    "get_source_page": "Texte d'une page d'un livre local (magasin de pages requis).",
    "search_source_pages": "Recherche d'un mot dans les pages locales (magasin de pages requis).",
}
LOCAL_STORE = {"get_source_page", "search_source_pages"}


async def run(requests: dict) -> dict:
    results = {}
    params = StdioServerParameters(
        command=str(ROOT / ".venv" / "bin" / "wirdi-mcp"), env={"WIRDI_MCP_LOG_LEVEL": "ERROR"}
    )
    async with Client(params, read_timeout_seconds=30) as client:
        for tool, request in requests.items():
            reply = await client.call_tool(tool, request["arguments"])
            results[tool] = reply.structured_content
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "EXEMPLES_REQUETES.md")
    args = parser.parse_args()
    apply = json.loads((ROOT / "docs" / "APPLY.json").read_text(encoding="utf-8"))
    first = {}
    for request in apply["requests"]:
        if request["expect"].get("status") != "error":
            first.setdefault(request["tool"], request)
    results = asyncio.run(run(first))
    lines = [
        "# Exemples de requêtes, un par outil",
        "",
        "Chaque bloc JSON est le contenu **complet** de `arguments`, accolades extérieures comprises : "
        "colle-le tel quel dans l'éditeur de l'Inspector (« Edit as JSON »), puis **Execute Tool**. "
        "Ne colle pas seulement `selection`.",
        "",
        "Chaque requête a été exécutée contre le serveur au moment de la génération du fichier "
        "(`scripts/build_examples_md.py`). Les numéros d'ayah sont ceux du compte Qaloun "
        "(6 214 ayat) : un numéro hors limites, comme 2:286, renvoie `INVALID_REFERENCE`.",
        "",
    ]
    for tool in ORDER:
        request = first[tool]
        result = results[tool]
        status = result.get("status")
        lines += [
            f"## `{tool}`",
            "",
            f"**Rôle.** {ROLE[tool]}",
            "",
            f"**Exemple.** {request['purpose']}",
            "",
            "```json",
            json.dumps(request["arguments"], ensure_ascii=False, indent=2),
            "```",
            "",
            f"**Résultat attendu.** `status: {status!r}`"
            + (
                "."
                if tool not in LOCAL_STORE
                else ". Il faut d'abord construire le magasin de pages local "
                "(`scripts/build_page_store.py`), sinon la réponse est `DATA_UNAVAILABLE`."
            ),
            "",
        ]
    lines += [
        "## Cas d'erreur utiles",
        "",
        "Les requêtes d'erreur (`INVALID_REFERENCE`, `NOT_FOUND`, `UNSUPPORTED_VERSION`…) sont dans "
        "`docs/APPLY.json`, avec le code attendu dans `expect`.",
        "",
    ]
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"wrote {args.out}; statuses: "
        + ", ".join(f"{t}={results[t].get('status')}" for t in ORDER)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
