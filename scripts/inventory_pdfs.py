#!/usr/bin/env python3
"""Read-only inventory of source PDFs: SHA-256, pdfinfo fields and text-layer shape.

Only metadata and character counts are reported; no page text is printed or stored.
Never opens a PDF for writing and never bypasses document protection.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SAMPLE_FIELDS = ("Title", "Author", "Creator", "Producer", "CreationDate", "Pages", "Encrypted")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(args: list[str]) -> str:
    done = subprocess.run(args, capture_output=True, text=True, check=False)
    return done.stdout


def pdfinfo(path: Path) -> dict[str, str]:
    info = {}
    for line in run(["pdfinfo", str(path)]).splitlines():
        key, _, value = line.partition(":")
        if key.strip() in SAMPLE_FIELDS:
            info[key.strip()] = value.strip()
    return info


def text_chars(path: Path, page: int) -> int:
    out = run(["pdftotext", "-f", str(page), "-l", str(page), str(path), "-"])
    return len(re.sub(r"\s", "", out))


def image_count(path: Path, page: int) -> int:
    rows = run(["pdfimages", "-list", "-f", str(page), "-l", str(page), str(path)]).splitlines()
    return max(len(rows) - 2, 0)


def inventory(path: Path) -> dict:
    info = pdfinfo(path)
    pages = int(info.get("Pages", "0") or 0)
    sample = sorted({p for p in (1, 2, 3, pages // 2, pages - 1, pages) if 1 <= p <= pages})
    encrypted = info.get("Encrypted", "")
    return {
        "file": path.name,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "pdfinfo": info,
        "protected_copy": "copy:no" in encrypted,
        # Text extraction is skipped for copy-protected documents; protection is respected.
        "sampled_pages": [
            {
                "pdf_page": p,
                "text_chars": None if "copy:no" in encrypted else text_chars(path, p),
                "images": image_count(path, p),
            }
            for p in sample
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path("docs"))
    parser.add_argument("--write", type=Path, help="write metadata-only JSON to this path")
    args = parser.parse_args()
    report = [inventory(p) for p in sorted(args.directory.glob("*.pdf"))]
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.write:
        args.write.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
