"""The bundled snapshot: pinned, public, small, and equal in behaviour to the originals."""

import json
import os
from pathlib import Path

import pytest

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.mapping.bridge import ReadOnlyAuthorityView, bind_authority
from wirdi_mcp.quran.source import SNAPSHOT_ROOT, PublicSourceRepository, digest

ROOT = Path(__file__).resolve().parents[2]
MAX_SNAPSHOT_BYTES = 6 * 1024 * 1024


def snapshot_files():
    return [p for p in SNAPSHOT_ROOT.rglob("*") if p.is_file()]


def test_every_bundled_artifact_matches_its_pinned_hash():
    repo = PublicSourceRepository.bundled()
    assert repo.source == "bundled"
    for relative, expected in repo.manifest["artifacts"].items():
        assert digest((SNAPSHOT_ROOT / relative).read_bytes()) == expected, relative
        assert repo.read_artifact(relative)


def test_bundled_load_gives_the_full_corpus_and_page_map():
    repo = PublicSourceRepository.bundled()
    assert len(repo.load_edition("qalun")) == 6214
    assert len(repo.load_pages()) == 6214


def test_a_modified_bundled_file_fails_closed(tmp_path):
    for p in snapshot_files():
        target = tmp_path / p.relative_to(SNAPSHOT_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())
    note = tmp_path / "docs/qaloun-pagination-validation.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nedited", encoding="utf-8")
    repo = PublicSourceRepository(tmp_path, "bundled")

    with pytest.raises(KnowledgeError) as error:
        repo.load_pages()
    assert error.value.error.code == "INTEGRITY_FAILURE"


def test_snapshot_has_no_local_path_or_app_internals_and_stays_small():
    total = 0
    for path in snapshot_files():
        data = path.read_bytes()
        total += len(data)
        assert path.suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
        if path.name in {"qalun.json", "qpc-hafs.json"}:
            continue
        text = data.decode("utf-8", errors="ignore")
        for forbidden in ("/home/", "OpenRouter", "najjar"):
            assert forbidden not in text, (path.name, forbidden)
    assert total < MAX_SNAPSHOT_BYTES


def test_licence_and_notice_files_ship_with_the_data():
    for name in ("NOTICE.md", "LICENSE-DATA.md"):
        assert (SNAPSHOT_ROOT / name).is_file(), name
    assert (SNAPSHOT_ROOT / "data/raw/quran-json/repo/LICENSE.txt").is_file()
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")


def test_trimmed_schemas_give_the_same_mapping_as_the_original_on_all_selections():
    original_root = os.environ.get("WIRDI_TEST_SOURCE_ROOT")
    if not original_root:
        pytest.skip("Set WIRDI_TEST_SOURCE_ROOT to compare with the original schemas")
    original = Path(original_root) / "backend/app/schemas.py"
    bundled = PublicSourceRepository.bundled()
    mapper = bundled.read_artifact("backend/app/tadabbur/mapping.py")
    arabic = bundled.read_artifact("backend/app/tadabbur/arabic.py")
    trimmed = bind_authority(mapper, arabic, bundled.read_artifact("backend/app/schemas.py"))
    full = bind_authority(mapper, arabic, original.read_bytes())
    rows = {eid: bundled.load_edition(eid) for eid in ("qalun", "hafs")}
    editions = {
        eid: {
            "source": meta["source"],
            "license": bundled.manifest["license"],
            "source_checksum": bundled.manifest["artifacts"][meta["path"]],
            "text_checksum": meta["text_sha256"],
        }
        for eid, meta in bundled.manifest["editions"].items()
    }
    view = ReadOnlyAuthorityView(rows, editions)
    checked = 0
    for row in rows["qalun"]:
        selected = view.select_qaloun(row.surah, row.number, row.number)
        a = trimmed(view, selected, "qalun", row.surah).model_dump()
        b = full(view, selected, "qalun", row.surah).model_dump()
        assert json.dumps(a, sort_keys=True, default=str) == json.dumps(
            b, sort_keys=True, default=str
        ), (row.surah, row.number)
        checked += 1
    assert checked == 6214
