"""Synthetic unit sources are generated locally; real-source checks are opt-in."""

import hashlib
import json
import os
from pathlib import Path

import pytest

from wirdi_mcp.domain.models import PassageSelection
from wirdi_mcp.quran.source import PublicSourceRepository


def selection(repo, surah=6, lo=1, hi=8):
    return PassageSelection(start=repo.reference("qalun", surah, lo), end_ayah=hi)


def target(repo):
    meta = repo.manifest["editions"]["hafs"]
    return {
        "target_corpus_id": meta["corpus_id"],
        "target_corpus_version": meta["version"],
        "target_numbering_system": meta["numbering_system"],
    }


@pytest.fixture
def synthetic_repo(tmp_path):
    """Non-Quran sentinels only. Production cannot select a different manifest."""
    repo = PublicSourceRepository(tmp_path)
    for edition in ("qalun", "hafs"):
        meta = repo.manifest["editions"][edition]
        doc = {
            str(s): [
                {
                    "chapter": s,
                    "verse": n,
                    "text": f"  SENTINEL e\u0301 {s}:{n}  ",
                    "number_in_hafs": [n],
                }
                for n in range(1, count + 1)
            ]
            for s, count in enumerate(meta["surah_counts"], 1)
        }
        raw = json.dumps(doc).encode()
        p = tmp_path / meta["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
        repo.manifest["artifacts"][meta["path"]] = sha
        meta["version"] = "sha256:" + sha
        meta["text_sha256"] = hashlib.sha256(
            "\n".join(v["text"] for verses in doc.values() for v in verses).encode()
        ).hexdigest()
    pages = [[1 + i * 558 // 6213] * 2 for i in range(6214)]
    doc = {
        "edition_id": "qalun",
        "page_count": 559,
        "verse_count": 6214,
        "reference": repo.manifest["pagination_reference"],
        "verse_pages": pages,
        "map_sha256": hashlib.sha256(json.dumps(pages).encode()).hexdigest(),
    }
    repo.manifest["pagination_sha256"] = doc["map_sha256"]
    paths = {
        repo.manifest["pagination_path"]: json.dumps(doc).encode(),
        "docs/qaloun-pagination-validation.md": b"Synthetic evidence only",
        "docs/day2-final-validation.md": b"Synthetic evidence only",
    }
    for rel, raw in paths.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        repo.manifest["artifacts"][rel] = hashlib.sha256(raw).hexdigest()
    return repo


@pytest.fixture(scope="session")
def real_repo():
    root = os.environ.get("WIRDI_TEST_SOURCE_ROOT")
    if not root:
        pytest.skip("Set WIRDI_TEST_SOURCE_ROOT for read-only real-source conformance checks")
    # An explicitly requested inaccessible source fails; it is never silently skipped.
    return PublicSourceRepository(Path(root))
