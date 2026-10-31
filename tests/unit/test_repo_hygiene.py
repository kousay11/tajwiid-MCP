import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff")


def tracked():
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    done = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return done.stdout.splitlines()


def test_no_source_book_scan_page_image_or_extracted_text_is_tracked():
    files = tracked()
    assert not [f for f in files if f.lower().endswith(FORBIDDEN)]
    assert not [f for f in files if "/pages" in f and f.startswith("knowledge/sources/")]
    assert not [
        f for f in files if f.startswith((".work/", "knowledge/derived/", "knowledge/mushaf/"))
    ]


def test_ignore_rules_cover_the_unknown_licence_material():
    ignored = subprocess.run(
        [
            "git",
            "check-ignore",
            "docs/x.pdf",
            "knowledge/sources/book-a-2010/pages.jsonl",
            "knowledge/sources/book-a-2010/pages_manifest.json",
            ".work/mushaf_pilot/page0001.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout.split()
    assert len(ignored) == 4
