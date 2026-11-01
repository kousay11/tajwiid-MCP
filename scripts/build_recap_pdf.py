#!/usr/bin/env python3
# ruff: noqa: E501
"""Write docs/RECAP_PROJET.pdf, a French summary of everything the project does and has done.

The figures (tools, rules, detectors, families) are read from the repository, so the summary cannot
drift from the code. The page is built as HTML and converted with LibreOffice (headless). The PDF is
git-ignored like every PDF of this repository: regenerate it with this script.

Usage: build_recap_pdf.py [--tests 322] [--clean-tests 289]
"""

import argparse
import collections
import html
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wirdi_mcp import __version__  # noqa: E402
from wirdi_mcp.tajwid.detectors import DETECTORS  # noqa: E402
from wirdi_mcp.tools.contracts import TOOL_CONTRACTS  # noqa: E402

TOOLS = {
    "health_check": "État du serveur et de la source du Coran (embarquée par défaut)",
    "get_qaloun_passage": "Ayat Qaloun inchangés, empreinte SHA-256, pages de la mise en page à 559 pages",
    "resolve_source_mapping": "Correspondance de la numérotation Qaloun vers Kufi/Hafs, avec statut de sûreté",
    "list_tajwid_rules": "Liste des règles, famille, type, présence d'un détecteur",
    "get_tajwid_rule": "Une fiche de règle : définition, conditions, limites, citations (livre et page)",
    "analyze_qaloun_tajwid": "Annotations candidates sur 1 à 100 ayat, paginées, avec contexte waqf/wasl",
    "summarize_tajwid": "Comptes par règle et par ayah pour une sourate ou une plage",
    "analyze_app_page": "Annotations des ayat qui commencent sur une page de l'application (1 à 559)",
    "list_reading_combinations": "Lectures permises ensemble dans un ayah (tables du livre, pp.98-108)",
    "get_letter_properties": "Makhraj et caractéristiques des lettres (livre A, pp.40-45)",
    "get_source_page": "Pages d'un livre placé en local (magasin de pages ignoré par git)",
    "search_source_pages": "Recherche d'un mot dans les pages locales, texte normalisé",
}
FAMILY_LABEL = {
    "madd": "Madd (naturel, badal, 'iwad, muttasil, munfasil, 'arid, lin, lazim, sila, alefs, أنا, الم الله, tawkid léger)",
    "hamza": "Hamza (remplacées, النبي, deux hamzas, interrogatif répété, hamzat al-wasl, أرأيت, avant l'article)",
    "tafkhim_tarqiq": "Tafkhim et tarqiq (ra, lam d'Allah, alef, ghunna, quatre rangs de l'isti'la)",
    "noon_sakina_tanween": "Noon sakina et tanwin (izhar, idgham, iqlab, ikhfa)",
    "mim_sakina": "Mim sakina (idgham, ikhfa, izhar shafawi)",
    "idgham_general": "Idgham général (mutamathilayn, mutajanisayn, mutaqaribayn, naqis, kabir)",
    "ya_idafa": "Ya de l'idafa (ouvert, fermé, معي, ربي)",
    "ya_zaida": "Ya zaida (conservé, deux lectures, conservé toujours) : livre Nabhan seul",
    "waqf": "Arrêts qui dépendent du rasm : ta ouvert, mots séparés, أيه, mot coupé : livre Nabhan seul",
    "lam_taarif": "Lam de l'article (solaire, lunaire)",
    "imala_taqlil": "Taqlil et imala",
    "qalqala": "Qalqala",
    "ghunna": "Ghunna du noon et du mim chaddés",
}
CSS = """
body { font-family: 'Noto Sans', 'DejaVu Sans', sans-serif; font-size: 10pt; color: #222; }
h1 { font-size: 22pt; color: #14532d; margin-bottom: 2pt; }
h2 { font-size: 14pt; color: #14532d; border-bottom: 1px solid #14532d; margin-top: 16pt; }
h3 { font-size: 11pt; color: #14532d; }
table { border-collapse: collapse; width: 100%; }
th { background: #14532d; color: #ffffff; text-align: left; padding: 3pt; font-size: 9pt; }
td { border-bottom: 1px solid #cccccc; padding: 3pt; vertical-align: top; font-size: 9pt; }
.k { background: #ecfdf5; padding: 6pt; }
.small { font-size: 8.5pt; color: #555; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt; }
"""


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def table(headers, rows, first_width: int = 0) -> str:
    """An HTML table; `first_width` is the width of the first column in percent."""
    width = f" width='{first_width}%'" if first_width else ""
    head = "".join(f"<th{width if k == 0 else ''}>{esc(h)}</th>" for k, h in enumerate(headers))
    body = "".join(
        "<tr>"
        + "".join(f"<td{width if k == 0 else ''}>{c}</td>" for k, c in enumerate(row))
        + "</tr>"
        for row in rows
    )
    return f"<table><tr>{head}</tr>{body}</table>"


def load_rules() -> list[dict]:
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((ROOT / "knowledge" / "rules").glob("*/1.json"))
    ]


def build_html(tests: int, clean_tests: int) -> str:
    rules = load_rules()
    families = collections.OrderedDict()
    for rule in rules:
        families.setdefault(rule["family"], []).append(rule["rule_id"])
    second = sum(
        1 for r in rules if any(c["edition_id"] == "thamar-yani-2003" for c in r["evidence"])
    )
    n_tools = len(TOOL_CONTRACTS) + 1  # health_check has no contract of its own
    parts: list[str] = []
    add = parts.append
    add(f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>")
    add("<h1>wirdi-mcp : récapitulatif du projet</h1>")
    add(
        f"<p class='small'>Version {esc(__version__)} · document généré le {date.today():%d/%m/%Y} "
        "par scripts/build_recap_pdf.py · les chiffres sont lus dans le dépôt</p>"
    )
    add(
        "<div class='k'><b>En une phrase.</b> Un serveur MCP local (stdio) qui lit le texte de la "
        "riwaya de Qaloun (d'après Nafi'), le met en rapport avec les règles de tajwid de deux "
        "livres, et renvoie des <b>annotations candidates</b> : la lettre exacte, la règle, la "
        "page citée et les lectures permises. Aucun modèle de langage, aucun réseau : du code "
        "déterministe, des fiches figées par empreinte SHA-256.</div>"
    )

    add("<h2>1. Chiffres clés</h2>")
    add(
        table(
            ["Élément", "Valeur"],
            [
                ["Outils MCP", f"{n_tools} (tous en lecture seule)"],
                ["Règles de tajwid (fiches)", f"{len(rules)} dans {len(families)} familles"],
                ["Détecteurs", f"{len(DETECTORS)} (une règle = un détecteur)"],
                [
                    "Citations",
                    f"Livre A pour {sum(1 for r in rules if any(c['edition_id'] == 'book-a-2010' for c in r['evidence']))} règles ; livre Nabhan pour {second} règles",
                ],
                ["Tests", f"{tests} (dont {clean_tests} sur un clone propre, sans dépôt Wirdi AI)"],
                [
                    "Corpus",
                    "6 214 ayat Qaloun, 559 pages, empreintes épinglées, embarqués dans le paquet",
                ],
                ["Statut maximal", "candidate : aucune annotation n'est vérifiée par un relecteur"],
                ["Licences", "Code MIT ; données du Coran CC BY-SA 4.0 (crédit Qur'anpedia.net)"],
            ],
        )
    )

    add("<h2>2. Les outils</h2>")
    add(
        table(
            ["Outil", "Ce qu'il fait"],
            [[f"<code>{n}</code>", esc(TOOLS[n])] for n in TOOLS],
            first_width=34,
        )
    )

    add("<h2>3. Les règles, par famille</h2>")
    rows = []
    for fam, ids in sorted(families.items(), key=lambda kv: -len(kv[1])):
        rows.append([f"<code>{fam}</code>", str(len(ids)), esc(FAMILY_LABEL.get(fam, ""))])
    add(table(["Famille", "Règles", "Contenu"], rows, first_width=26))
    add(
        "<p class='small'>Chaque fiche est une paraphrase courte écrite pour ce projet, avec ses "
        "conditions, ses exceptions, ses limites et la page citée. Le tableau complet des règles est "
        "dans le README.</p>"
    )

    add("<h2>4. Ce qui a été fait, dans l'ordre</h2>")
    add(
        table(
            ["Étape", "Résultat"],
            [
                [
                    "Mission 0.5.0",
                    "Serveur MCP, 14 règles de tajwid (noon, mim, lam, qalqala, ghunna), contrats "
                    "typés, intégrité par SHA-256, détection candidate seulement.",
                ],
                [
                    "Livre A complet (0.6.0)",
                    "Madd, hamza, tafkhim, idgham, ya de l'idafa, taqlil : 81 règles, 79 détecteurs, "
                    "citations vérifiées sur les images des pages, README et APPLY.json "
                    "(une requête prête à coller par outil).",
                ],
                [
                    "Projet autonome",
                    "Texte du Coran, pagination 559 pages et résolveur de correspondance embarqués "
                    "(snapshot épinglé) : un clone propre teste tous les outils. Licences MIT et "
                    "CC BY-SA 4.0, NOTICE.",
                ],
                [
                    "Nettoyage",
                    "Source unique : le livre A. Retrait de l'outil d'explication jamais implémenté, "
                    "du code de détection par couleur du mushaf, du livre B, des documents de travail.",
                ],
                [
                    "Règles ajoutées du livre A",
                    "Qalqala fusionnée en une règle ; rangs de l'isti'la, alef après ra, tawkid léger, "
                    "الم الله, أرأيت, hamzat al-wasl suivie d'une hamza qat'.",
                ],
                [
                    "Deuxième livre (Nabhan, 214 p.)",
                    f"Enregistré comme source (métadonnées seulement). {second} règles reçoivent une "
                    "seconde citation ; les variantes manquantes sont ajoutées ; ya zaida et hamza "
                    "d'interrogation avant l'article ajoutés. Le livre A en est un résumé : ce n'est "
                    "pas une preuve indépendante, et c'est écrit dans chaque fiche.",
                ],
                [
                    "Trois chantiers du deuxième livre",
                    "Outil <code>list_reading_combinations</code> (tables du livre, comptes reproduits) ; "
                    "lecture des tableaux de farsh (1 267 lignes) pour détecter deux hamzas dans deux mots "
                    "et la voyelle d'une lettre sakin avant la hamza wasla, lieu par lieu ; quatre règles "
                    "d'arrêt liées au rasm.",
                ],
            ],
        )
    )

    add("<h2>5. Vérifications effectuées</h2>")
    add(
        "<ul>"
        f"<li><b>Tests</b> : {tests} au total, dont {clean_tests} sur un clone propre "
        "(archive git, environnement neuf, aucune variable, aucun accès à Wirdi AI) ; ruff et "
        "contrôle du manifeste des règles verts.</li>"
        "<li><b>Corpus entier</b> : chaque règle est exécutée sur les 6 214 ayat, en waqf et en wasl ; "
        "les listes fermées du livre doivent toucher exactement les lieux nommés.</li>"
        "<li><b>Citations</b> : lues sur les images des pages, pas seulement dans le texte extrait.</li>"
        "<li><b>Tables des combinaisons</b> : les tests retrouvent chaque nombre que le livre énonce "
        "(4, 7, 6, 11, 10, 18 lectures, etc.).</li>"
        "<li><b>Tableaux de farsh contre les détecteurs du ya</b> : sur 182 lieux, aucun ya du locuteur "
        "à l'intérieur d'un ayah n'est manquant ; les écarts sont des verbes ou des paires à cheval "
        "sur deux ayat.</li>"
        "<li><b>Livre contre corpus</b> : les écarts de rasm sont listés (أن لا 21:87, كل ما 4:91, "
        "بئس ما…), sans rien modifier ni arbitrer.</li>"
        "</ul>"
    )

    add("<h2>6. Choix et limites à connaître</h2>")
    add(
        "<ul>"
        "<li><b>Rien n'est un verdict.</b> Les fiches sont paraphrasées par un rédacteur automatique ; "
        "aucun relecteur qualifié n'a rien validé : statut maximal <code>candidate</code>.</li>"
        "<li><b>Transmission</b> : toutes les règles restent <code>unspecified</code> ; le livre "
        "Nabhan ne nomme Abu Nashit qu'à la p.111, au-dessus des tableaux de farsh.</li>"
        "<li><b>Les lectures multiples ne sont jamais départagées</b> : elles sont listées dans "
        "<code>variants</code>. Le livre se contredit parfois (فألقه) : les deux lectures restent.</li>"
        "<li><b>Le texte Qaloun ne change jamais</b> ; aucune règle de Hafs n'est supposée.</li>"
        "<li><b>Combinaisons à trois madds ou plus</b> : extension des tables par paires du livre, "
        "marquée comme inférence (<code>pairwise_extension</code>).</li>"
        "<li><b>Deux hamzas dans deux mots et lettre sakin avant la hamza wasla</b> : trouvées "
        "seulement aux lieux des tableaux de farsh que le corpus montre ; ailleurs le texte ne garde "
        "que le résultat.</li>"
        "<li><b>Non construits</b> : arrêts au choix, rawm, ishmam (le moteur ne s'arrête qu'en fin "
        "d'ayah), ya fermé par défaut avant une lettre ordinaire (il faudrait la liste de tous les ya "
        "de l'idafa).</li>"
        "<li><b>Aucun PDF, image ni texte de livre dans git</b> ; les livres restent locaux.</li>"
        "</ul>"
    )

    add("<h2>7. Utiliser le projet</h2>")
    add(
        "<pre style='font-size:8.5pt'>"
        "python3 -m venv .venv &amp;&amp; .venv/bin/pip install -e '.[dev]'\n"
        ".venv/bin/wirdi-mcp                      # serveur stdio, aucune configuration\n"
        "npx @modelcontextprotocol/inspector .venv/bin/wirdi-mcp\n"
        ".venv/bin/python -m pytest               # tout le suivi, sur le snapshot embarqué\n"
        ".venv/bin/python scripts/verify_local.py # contrôle de bout en bout\n"
        "</pre>"
        "<p>Les requêtes prêtes à coller sont dans <code>docs/APPLY.json</code> (une par outil au "
        "moins, vérifiées par un test). Les règles, avec leurs pages, sont dans le README.</p>"
    )

    add("<h2>8. Suite possible</h2>")
    add(
        "<ul>"
        "<li>Commiter puis pousser le dépôt (aucun push n'a été fait) et refaire la simulation de "
        "clone propre.</li>"
        "<li>Trouver un relecteur qualifié : seul moyen de sortir du statut <code>candidate</code>.</li>"
        "<li>Intégrer le serveur dans l'application (<code>wirdi-Ai</code>), en affichant les "
        "annotations comme non vérifiées. Non commencé.</li>"
        "<li>Compléter les tableaux de farsh restants et les arrêts au choix si le moteur gagne un "
        "contexte d'arrêt.</li>"
        "</ul>"
    )
    add("</body></html>")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", type=int, default=322)
    parser.add_argument("--clean-tests", type=int, default=289)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "RECAP_PROJET.pdf")
    args = parser.parse_args()
    soffice = shutil.which("soffice")
    if soffice is None:
        raise SystemExit("LibreOffice (soffice) is needed to write the PDF")
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "RECAP_PROJET.html"
        source.write_text(build_html(args.tests, args.clean_tests), encoding="utf-8")
        subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf:writer_web_pdf_Export",
                "--outdir",
                tmp,
                str(source),
            ],
            check=True,
            capture_output=True,
        )
        args.out.write_bytes((Path(tmp) / "RECAP_PROJET.pdf").read_bytes())
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
