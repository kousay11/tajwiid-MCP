import hashlib
import json

import pytest
from conftest import REPO_KNOWLEDGE

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.knowledge.registry import RuleRegistry
from wirdi_mcp.tajwid.detectors import DETECTORS


def code(exc_info):
    return exc_info.value.error.code


def test_every_committed_rule_loads_and_every_citation_resolves():
    registry = RuleRegistry(REPO_KNOWLEDGE)
    listed = registry.list_rules()
    # every detector has a record; the only records without one are the two Book A rules whose
    # inputs the Qaloun text no longer carries (the original hamzas of two adjacent words)
    assert {r for r, _ in listed} - set(DETECTORS) == {
        "hamza_two_words_same",
        "hamza_two_words_different",
    }
    assert set(DETECTORS) <= {r for r, _ in listed} and len(listed) == 79
    for rule_id, version in listed:
        rule = registry.get_rule(rule_id, version)
        assert rule.validation_status == "unreviewed" and rule.validation_record_ids == ()
        assert rule.evidence and all(c.validation_status == "unreviewed" for c in rule.evidence)
        # book and page are named in every citation
        assert all(c.locator.startswith(("p.", "printed p.")) for c in rule.evidence)


def test_manifest_script_check_passes_on_the_committed_state():
    import subprocess
    import sys

    done = subprocess.run(
        [sys.executable, "scripts/build_rule_manifest.py", "--check"],
        cwd=REPO_KNOWLEDGE.parent,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr


def test_one_changed_byte_in_a_rule_fails_closed(knowledge_copy):
    path = knowledge_copy / "rules" / "iqlab" / "1.json"
    raw = bytearray(path.read_bytes())
    raw[-3] ^= 1
    path.write_bytes(bytes(raw))
    with pytest.raises(KnowledgeError) as exc_info:
        RuleRegistry(knowledge_copy).get_rule("iqlab", "1")
    assert code(exc_info) == "INTEGRITY_FAILURE"
    # other rules stay readable: the failure is per record
    assert RuleRegistry(knowledge_copy).get_rule("idhar_halqi", "1").rule_id == "idhar_halqi"


def test_changed_edition_metadata_fails_closed(knowledge_copy):
    path = knowledge_copy / "sources" / "editions.json"
    path.write_text(path.read_text("utf-8").replace("1431", "1432"), "utf-8")
    with pytest.raises(KnowledgeError) as exc_info:
        RuleRegistry(knowledge_copy).get_rule("iqlab", "1")
    assert code(exc_info) == "INTEGRITY_FAILURE"


def test_citation_to_a_page_outside_the_edition_does_not_resolve(knowledge_copy):
    path = knowledge_copy / "rules" / "iqlab" / "1.json"
    doc = json.loads(path.read_text("utf-8"))
    doc["evidence"][0]["locator"] = "p.900"
    raw = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode()
    path.write_bytes(raw)
    manifest_path = knowledge_copy / "rules" / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    for entry in manifest["rules"]:
        if entry["rule_id"] == "iqlab":
            entry["sha256"] = hashlib.sha256(raw).hexdigest()
    manifest_path.write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(KnowledgeError) as exc_info:
        RuleRegistry(knowledge_copy).get_rule("iqlab", "1")
    assert code(exc_info) == "INTEGRITY_FAILURE"


@pytest.mark.parametrize(
    ("rule_id", "version", "expected"),
    [
        ("no_such_rule", "1", "NOT_FOUND"),
        ("iqlab", "2", "UNSUPPORTED_VERSION"),
        ("../../etc/passwd", "1", "NOT_FOUND"),
        ("iqlab", "../1", "NOT_FOUND"),
    ],
)
def test_lookup_errors_are_typed_and_path_safe(rule_id, version, expected):
    with pytest.raises(KnowledgeError) as exc_info:
        RuleRegistry(REPO_KNOWLEDGE).get_rule(rule_id, version)
    assert code(exc_info) == expected


def test_missing_store_is_unavailable_not_a_crash(tmp_path):
    for root in (None, tmp_path):
        with pytest.raises(KnowledgeError) as exc_info:
            RuleRegistry(root).get_rule("iqlab", "1")
        assert code(exc_info) == "DATA_UNAVAILABLE"
        assert str(tmp_path) not in str(exc_info.value)
