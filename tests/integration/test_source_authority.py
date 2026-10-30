"""Opt-in conformance against the existing public source files; never a database."""

import hashlib
import json
from collections import Counter
from dataclasses import replace

import pytest
from conftest import selection, target

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.mapping.adapter import WirdiSourceMappingAdapter
from wirdi_mcp.mapping.bridge import ReadOnlyAuthorityView, bind_authority
from wirdi_mcp.quran.source import QalounFileAdapter


def original_resolver(repo):
    return bind_authority(
        repo.read_artifact("backend/app/tadabbur/mapping.py"),
        repo.read_artifact("backend/app/tadabbur/arabic.py"),
        repo.read_artifact("backend/app/schemas.py"),
    )


def view_for(repo):
    rows = {eid: repo.load_edition(eid) for eid in ("qalun", "hafs")}
    editions = {
        eid: {
            "source": meta["source"],
            "license": repo.manifest["license"],
            "source_checksum": repo.manifest["artifacts"][meta["path"]],
            "text_checksum": meta["text_sha256"],
        }
        for eid, meta in repo.manifest["editions"].items()
    }
    return ReadOnlyAuthorityView(rows, editions)


@pytest.mark.parametrize(
    "s,lo,hi,status,kind,ranges",
    [
        (6, 1, 8, "verified_difference", "mixed", [(1, 7)]),
        (112, 1, 1, "verified_equivalent", "exact", [(1, 1)]),
        (1, 1, 1, "verified_difference", "numbering", [(2, 2)]),
        (2, 1, 1, "verified_difference", "one_to_many", [(1, 2)]),
        (2, 253, 254, "verified_difference", "many_to_one", [(255, 255)]),
        (6, 1, 1, "verified_difference", "many_to_one", [(1, 1)]),
        (2, 27, 27, "mapping_requires_review", "unverified", [(28, 28)]),
    ],
)
def test_existing_boundary_cases(real_repo, s, lo, hi, status, kind, ranges):
    result = WirdiSourceMappingAdapter(real_repo).resolve_sync(
        selection(real_repo, s, lo, hi),
        **target(real_repo),
    )
    assert result.mapping_status == status and result.mapping_type == kind
    assert [(r.start.ayah, r.end_ayah) for r in result.source_reference] == ranges
    assert result.safe_for_source_retrieval == (status != "mapping_requires_review")
    if s == 6:
        assert result.components[0].qaloun_ayat == (1, 2)
        assert result.components[0].source_ayat == (1,)
        assert result.components[0].includes_context_outside_selection == (hi == 1)


@pytest.mark.parametrize(
    "links,expected", [((), "missing"), ((999,), "unverified"), ((1, 3), "ambiguous")]
)
def test_original_unresolved_behavior_without_source_mutation(real_repo, links, expected):
    view = view_for(real_repo)
    # Only detached synthetic in-memory links change; no real corpus file is edited.
    view.rows["qalun"] = tuple(
        replace(r, links=links) if (r.surah, r.number) == (112, 1) else r
        for r in view.rows["qalun"]
    )
    result = original_resolver(real_repo)(view, view.select_qaloun(112, 1, 1), "qalun", 112)
    assert result.mapping_status == "mapping_requires_review"
    assert result.mapping_type == expected and result.reasons
    if not links:
        assert result.source_reference == []


def test_ambiguous_many_to_many_is_not_promoted(real_repo):
    view = view_for(real_repo)
    view.rows["qalun"] = tuple(
        replace(r, links=(1, 2)) if r.surah == 112 and r.number in (1, 2) else r
        for r in view.rows["qalun"]
    )
    result = original_resolver(real_repo)(view, view.select_qaloun(112, 1, 2), "qalun", 112)
    assert result.mapping_status == "mapping_requires_review"
    assert result.mapping_type == "ambiguous"


def test_complete_single_ayah_conformance_against_existing_audit(real_repo):
    repo = real_repo
    audit = json.loads(repo.read_artifact("docs/reader-correction-mapping-audit.json"))
    resolver = original_resolver(repo)
    view = view_for(repo)
    counts = Counter()
    review = []
    for surah in range(1, 115):
        for row in view.select_qaloun(surah, 1, 1000):
            result = resolver(view, [row], "qalun", surah)
            counts[result.mapping_status] += 1
            if result.mapping_status == "mapping_requires_review":
                review.append(
                    {
                        "surah": surah,
                        "ayah": row.number,
                        "source_reference": [r.model_dump() for r in result.source_reference],
                        "reasons": result.reasons,
                    }
                )
    assert dict(counts) == audit["counts"]
    assert review == audit["requires_review"]


def test_real_text_pages_and_files_are_unchanged(real_repo):
    repo = real_repo
    paths = [repo.root / p for p in repo.manifest["artifacts"]]
    before = {p: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in paths}
    rows = repo.load_edition("qalun")
    pages = repo.load_pages()
    assert len(rows) == 6214 and len(pages) == 6214
    assert sum(a != b for a, b in pages) == 459
    # All 6,214 returned texts are compared directly with the original JSON strings.
    original = json.loads(repo.read_artifact(repo.manifest["editions"]["qalun"]["path"]))
    reader = QalounFileAdapter(repo)
    for surah in range(1, 115):
        count = len(original[str(surah)])
        for lo in range(1, count + 1, 100):
            passage = reader.read_passage(selection(repo, surah, lo, min(lo + 99, count)))
            assert [a.text for a in passage.ayat] == [
                v["text"] for v in original[str(surah)][lo - 1 : lo + 99]
            ]
    assert len(reader.read_passage(selection(repo, 7, 39, 39)).ayat) == 1
    row = reader.read_passage(selection(repo, 7, 39, 39)).ayat[0]
    assert (row.page_start, row.page_end) == (135, 136)
    assert before == {
        p: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in paths
    }


def test_target_identity_is_never_inferred(real_repo):
    with pytest.raises(KnowledgeError) as error:
        WirdiSourceMappingAdapter(real_repo).resolve_sync(
            selection(real_repo), "unknown", "unknown", "unknown"
        )
    assert error.value.error.code == "UNSUPPORTED_VERSION"
