"""Storage-independent draft records; no scholarly assertions are seeded."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from wirdi_mcp.domain.models import Citation, ContractModel, NonEmpty, Sha256, ValidationStatus


class ScholarlySource(ContractModel):
    source_id: NonEmpty
    title: NonEmpty
    responsible_party: NonEmpty


class SourceEdition(ContractModel):
    edition_id: NonEmpty
    source_id: NonEmpty
    publication: NonEmpty
    license_status: Literal["unknown", "authorized", "restricted"]
    license_reference: NonEmpty
    artifact_sha256: Sha256
    provenance_version: NonEmpty


class RuleClause(ContractModel):
    clause_id: NonEmpty
    kind: Literal["condition", "exception"]
    description: str
    evidence: Annotated[tuple[Citation, ...], Field(min_length=1)]


class TajwidRule(ContractModel):
    rule_id: NonEmpty
    version: NonEmpty
    name_ar: NonEmpty
    definition: str
    riwaya: Literal["qaloun"]
    # Book A names no tariq, so every rule is "unspecified"; the corpus itself is unspecified too.
    tariq: Literal["abu_nashit", "unspecified"]
    family: NonEmpty = "unclassified"
    # A: mechanical, B: depends on wasl/waqf or the neighbouring word, C: Qaloun lexical list.
    detectability: Literal["A", "B", "C"] = "A"
    limitations: tuple[str, ...] = ()
    conditions: tuple[RuleClause, ...]
    exceptions: tuple[RuleClause, ...]
    evidence: Annotated[tuple[Citation, ...], Field(min_length=1)]
    validation_status: ValidationStatus
    validation_record_ids: tuple[NonEmpty, ...]


class ValidationRecord(ContractModel):
    record_id: NonEmpty
    subject_id: NonEmpty
    subject_version: NonEmpty
    subject_sha256: Sha256
    reviewer_id: NonEmpty
    review_kind: Literal["structural", "integrity", "scholarly"]
    decision: Literal["approved", "rejected", "needs_review"]
    reviewed_at: datetime
    rationale: str
    evidence: Annotated[tuple[Citation, ...], Field(min_length=1)]
