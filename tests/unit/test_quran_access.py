import hashlib
import json

import pytest
from conftest import selection
from pydantic import ValidationError

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.domain.models import PassageSelection
from wirdi_mcp.quran.source import PublicSourceRepository, QalounFileAdapter


def test_exact_text_unicode_and_whitespace_preserved(synthetic_repo):
    repo = synthetic_repo
    result = QalounFileAdapter(repo).read_passage(selection(repo))
    expected = "  SENTINEL e\u0301 6:1  "
    assert len(result.ayat) == 8
    assert result.ayat[0].text == expected
    assert result.ayat[0].text_sha256 == hashlib.sha256(expected.encode()).hexdigest()
    assert result.corpus_text_sha256 == repo.manifest["editions"]["qalun"]["text_sha256"]
    assert result.pagination_status == "verified_against_edition"
    assert result.ayat[0].reference.tariq == "unspecified"


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("corpus_id", "another", "UNSUPPORTED_VERSION"),
        ("corpus_version", "another", "UNSUPPORTED_VERSION"),
        ("numbering_system", "hafs", "INVALID_REFERENCE"),
        ("tariq", "abu_nashit", "UNSUPPORTED_CONTEXT"),
    ],
)
def test_rejects_wrong_corpus_identity(synthetic_repo, field, value, code):
    data = selection(synthetic_repo).model_dump()
    data["start"][field] = value
    with pytest.raises(KnowledgeError) as error:
        QalounFileAdapter(synthetic_repo).read_passage(PassageSelection.model_validate(data))
    assert error.value.error.code == code


def test_qaloun_surah_bounds_do_not_use_hafs_counts(synthetic_repo):
    repo = synthetic_repo
    with pytest.raises(KnowledgeError) as error:
        QalounFileAdapter(repo).read_passage(selection(repo, 2, 286, 286))
    assert error.value.error.code == "INVALID_REFERENCE"
    with pytest.raises(ValidationError):
        repo.reference("qalun", 0, 1)


@pytest.mark.parametrize("artifact", ["corpus", "pagination", "evidence"])
def test_changed_files_fail_closed_without_rewriting(synthetic_repo, artifact):
    repo = synthetic_repo
    path = {
        "corpus": repo.manifest["editions"]["qalun"]["path"],
        "pagination": repo.manifest["pagination_path"],
        "evidence": "docs/day2-final-validation.md",
    }[artifact]
    p = repo.root / path
    changed = p.read_bytes() + b" "
    p.write_bytes(changed)
    with pytest.raises(KnowledgeError) as error:
        QalounFileAdapter(repo).read_passage(selection(repo))
    assert error.value.error.code == "INTEGRITY_FAILURE"
    assert p.read_bytes() == changed


def test_text_hash_and_pagination_array_hash_are_independent(synthetic_repo):
    repo = synthetic_repo
    repo.manifest["editions"]["qalun"]["text_sha256"] = "0" * 64
    with pytest.raises(KnowledgeError, match="Ordered Quran text"):
        QalounFileAdapter(repo).read_passage(selection(repo))


def test_pagination_semantics_checked_after_file_hash(synthetic_repo):
    repo = synthetic_repo
    p = repo.root / repo.manifest["pagination_path"]
    doc = json.loads(p.read_bytes())
    doc["page_count"] = 604
    raw = json.dumps(doc).encode()
    p.write_bytes(raw)
    repo.manifest["artifacts"][repo.manifest["pagination_path"]] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(KnowledgeError, match="pagination identity"):
        QalounFileAdapter(repo).read_passage(selection(repo))


def test_missing_configuration_or_files_has_safe_error(tmp_path):
    for root in (None, tmp_path):
        repo = PublicSourceRepository(root)
        with pytest.raises(KnowledgeError) as error:
            QalounFileAdapter(repo).read_passage(selection(repo))
        assert error.value.error.code == "DATA_UNAVAILABLE"
        assert str(tmp_path) not in str(error.value)


def test_source_reader_is_independent_from_hafs_and_mapper(synthetic_repo):
    repo = synthetic_repo
    (repo.root / repo.manifest["editions"]["hafs"]["path"]).unlink()
    assert len(QalounFileAdapter(repo).read_passage(selection(repo)).ayat) == 8


def test_no_data_mutation(synthetic_repo):
    repo = synthetic_repo
    before = {
        p: (p.read_bytes(), p.stat().st_mtime_ns) for p in repo.root.rglob("*") if p.is_file()
    }
    QalounFileAdapter(repo).read_passage(selection(repo))
    after = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in repo.root.rglob("*") if p.is_file()}
    assert before == after


def test_changed_authority_is_rejected_before_execution(tmp_path):
    repo = PublicSourceRepository(tmp_path)
    path = tmp_path / "backend/app/tadabbur/mapping.py"
    path.parent.mkdir(parents=True)
    path.write_text("raise AssertionError('must never execute changed authority')")
    with pytest.raises(KnowledgeError) as error:
        repo.read_artifact("backend/app/tadabbur/mapping.py")
    assert error.value.error.code == "INTEGRITY_FAILURE"
