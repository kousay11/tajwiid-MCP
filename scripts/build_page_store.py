#!/usr/bin/env python3
"""Build a LOCAL, git-ignored page store from a PDF that has a real text layer.

Refuses copy-protected PDFs: protection is never bypassed. The output is raw
`pdftotext` text (book A has inverted lam-alef ligatures and needs review); it is not
cleaned, so source text is never silently rewritten.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIDI = re.compile("[‪-‮‎‏⁦-⁩]")


def run(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("edition_id")
    parser.add_argument("--knowledge", type=Path, default=ROOT / "knowledge")
    args = parser.parse_args()

    editions = json.loads((args.knowledge / "sources" / "editions.json").read_text("utf-8"))
    edition = next(e for e in editions["editions"] if e["edition_id"] == args.edition_id)
    pdf_sha = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    if pdf_sha != edition["artifact_sha256"]:
        raise SystemExit("PDF does not match the registered edition checksum")
    if "copy:no" in run(["pdfinfo", str(args.pdf)]):
        raise SystemExit("This PDF is copy-protected; text extraction is not performed")

    pages = []
    for page in range(1, edition["page_count"] + 1):
        text = run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(args.pdf), "-"])
        pages.append({"pdf_page": page, "text": BIDI.sub("", text).strip()})
    out = args.knowledge / "sources" / args.edition_id
    out.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pages).encode("utf-8")
    (out / "pages.jsonl").write_bytes(body)
    manifest = {
        "edition_id": args.edition_id,
        "page_count": len(pages),
        "pages_sha256": hashlib.sha256(body).hexdigest(),
        "text_quality": "raw_pdftotext_lamalef_inverted_unreviewed",
    }
    (out / "pages_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    print(f"wrote {len(pages)} pages to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
