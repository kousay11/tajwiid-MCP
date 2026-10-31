"""Hash-pinned local registry of Tajwid rule records and source-edition metadata.

Every read re-verifies file digests against `knowledge/rules/manifest.json`, so a changed
byte fails closed with INTEGRITY_FAILURE. Rule citations are resolved against the source
edition metadata (edition known, page inside the edition, printed/pdf offset consistent).
"""

import hashlib
import json
import re
from pathlib import Path

from pydantic import ValidationError

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.domain.models import Citation
from wirdi_mcp.knowledge.models import TajwidRule

RULE_ID = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]{0,31}$")
LOCATOR = re.compile(r"^(?:printed )?p\.(\d{1,4})(?: \(pdf p\.(\d{1,4})\))?$")
MAX_FILE_BYTES = 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RuleRegistry:
    def __init__(self, root: Path | None):
        self.root = root

    def _read(self, relative: str) -> bytes:
        if self.root is None:
            raise KnowledgeError("DATA_UNAVAILABLE", "The local knowledge store is not configured")
        try:
            root = self.root.resolve(strict=True)
            path = (root / relative).resolve(strict=True)
            if not path.is_relative_to(root):
                raise KnowledgeError("INTEGRITY_FAILURE", "Knowledge file escapes its store")
            with path.open("rb") as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
        except (OSError, RuntimeError):
            raise KnowledgeError(
                "DATA_UNAVAILABLE", "A required local knowledge file is unreadable"
            ) from None
        if len(data) > MAX_FILE_BYTES:
            raise KnowledgeError("INTEGRITY_FAILURE", "Knowledge file exceeds its size limit")
        return data

    def manifest(self) -> dict:
        try:
            doc = json.loads(self._read("rules/manifest.json"))
            entries = doc["rules"]
            doc["editions_sha256"]
        except (ValueError, KeyError, TypeError):
            raise KnowledgeError("INTEGRITY_FAILURE", "The rule manifest is malformed") from None
        if not isinstance(entries, list):
            raise KnowledgeError("INTEGRITY_FAILURE", "The rule manifest is malformed")
        return doc

    def editions(self) -> dict[str, dict]:
        raw = self._read("sources/editions.json")
        if digest(raw) != self.manifest()["editions_sha256"]:
            raise KnowledgeError("INTEGRITY_FAILURE", "Source edition metadata checksum mismatch")
        try:
            return {e["edition_id"]: e for e in json.loads(raw)["editions"]}
        except (ValueError, KeyError, TypeError):
            raise KnowledgeError(
                "INTEGRITY_FAILURE", "Source edition metadata is malformed"
            ) from None

    def list_rules(self) -> tuple[tuple[str, str], ...]:
        return tuple((e["rule_id"], e["version"]) for e in self.manifest()["rules"])

    def get_rule(self, rule_id: str, version: str) -> TajwidRule:
        if not RULE_ID.fullmatch(rule_id) or not VERSION.fullmatch(version):
            raise KnowledgeError("NOT_FOUND", "No such local Tajwid rule")
        entries = [e for e in self.manifest()["rules"] if e["rule_id"] == rule_id]
        if not entries:
            raise KnowledgeError("NOT_FOUND", "No such local Tajwid rule")
        entry = next((e for e in entries if e["version"] == version), None)
        if entry is None:
            raise KnowledgeError("UNSUPPORTED_VERSION", "Rule version is not available locally")
        raw = self._read(entry["path"])
        if digest(raw) != entry["sha256"]:
            raise KnowledgeError("INTEGRITY_FAILURE", "Rule record checksum mismatch")
        try:
            rule = TajwidRule.model_validate_json(raw)
        except ValidationError:
            raise KnowledgeError("INTEGRITY_FAILURE", "Rule record is malformed") from None
        if (rule.rule_id, rule.version) != (rule_id, version):
            raise KnowledgeError("INTEGRITY_FAILURE", "Rule record identity mismatch")
        editions = self.editions()
        for citation in iter_citations(rule):
            check_citation(citation, editions)
        return rule


def iter_citations(rule: TajwidRule):
    yield from rule.evidence
    for clause in (*rule.conditions, *rule.exceptions):
        yield from clause.evidence


def check_citation(citation: Citation, editions: dict[str, dict]) -> None:
    """The cited edition must exist and the page must fall inside it."""
    edition = editions.get(citation.edition_id)
    match = LOCATOR.fullmatch(citation.locator)
    if edition is None or match is None:
        raise KnowledgeError("INTEGRITY_FAILURE", "A rule citation does not resolve")
    page = int(match.group(1))
    pdf_page = int(match.group(2)) if match.group(2) else page + edition["page_label_offset"]
    if (
        pdf_page != page + edition["page_label_offset"]
        or not 1 <= pdf_page <= edition["page_count"]
        or citation.source_id != edition["source_id"]
        or citation.provenance_version != "sha256:" + edition["artifact_sha256"]
    ):
        raise KnowledgeError("INTEGRITY_FAILURE", "A rule citation does not resolve")
