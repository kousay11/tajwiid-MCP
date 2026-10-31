"""Draft v1 contracts. Structural validity is never scholarly verification."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmpty = Annotated[str, Field(min_length=1, max_length=512)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
PositiveInt = Annotated[int, Field(strict=True, ge=1)]
ValidationStatus = Literal[
    "unreviewed", "machine_checked", "scholarly_verified", "rejected", "not_applicable"
]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class QuranReference(ContractModel):
    corpus_id: NonEmpty
    corpus_version: NonEmpty
    numbering_system: NonEmpty
    riwaya: NonEmpty
    tariq: NonEmpty
    surah: Annotated[int, Field(strict=True, ge=1, le=114)]
    ayah: PositiveInt


class QalounReference(QuranReference):
    riwaya: Literal["qaloun"]
    tariq: Literal["abu_nashit", "unspecified"]


class PassageSelection(ContractModel):
    start: QalounReference
    end_ayah: PositiveInt

    @model_validator(mode="after")
    def bounded_range(self) -> "PassageSelection":
        if not self.start.ayah <= self.end_ayah < self.start.ayah + 100:
            raise ValueError("Select 1 to 100 ayat within one surah")
        return self


class Citation(ContractModel):
    source_id: NonEmpty
    edition_id: NonEmpty
    title: NonEmpty
    responsible_party: NonEmpty
    publication: NonEmpty
    locator: NonEmpty  # page, section, or stable digital record identifier
    riwaya: NonEmpty
    tariq: NonEmpty
    provenance_version: NonEmpty
    validation_status: ValidationStatus
    uri: str | None = None


class Provenance(ContractModel):
    origin_id: NonEmpty
    origin_version: NonEmpty
    content_sha256: Sha256
    citations: tuple[Citation, ...] = ()
    retrieved_at: datetime | None = None


class Ayah(ContractModel):
    reference: QalounReference
    text: Annotated[str, Field(min_length=1)]
    text_sha256: Sha256
    provenance: Provenance
    page_start: Annotated[int, Field(strict=True, ge=1, le=559)] | None = None
    page_end: Annotated[int, Field(strict=True, ge=1, le=559)] | None = None


class Passage(ContractModel):
    selection: PassageSelection
    ayat: tuple[Ayah, ...]
    snapshot_sha256: Sha256
    corpus_text_sha256: Sha256
    pagination_sha256: Sha256
    pagination_status: Literal["verified_against_edition"]
    tariq_attestation: Literal["not_established_by_inspected_metadata"]


class SourcePassage(ContractModel):
    start: QuranReference
    end_ayah: PositiveInt


class MappingComponent(ContractModel):
    qaloun_ayat: tuple[PositiveInt, ...]
    source_ayat: tuple[PositiveInt, ...]
    type: Literal["exact", "numbering", "one_to_many", "many_to_one", "many_to_many"]
    textual_boundary_verified: bool
    includes_context_outside_selection: bool


class SourceMapping(ContractModel):
    qaloun_reference: PassageSelection
    source_reference: tuple[SourcePassage, ...]
    mapping_status: Literal["verified_equivalent", "verified_difference", "mapping_requires_review"]
    mapping_type: Literal[
        "exact",
        "numbering",
        "one_to_many",
        "many_to_one",
        "many_to_many",
        "mixed",
        "missing",
        "unverified",
        "ambiguous",
    ]
    mapping_version: NonEmpty
    mapping_artifact_sha256: Sha256
    components: tuple[MappingComponent, ...]
    source_provenance: dict[str, object]
    requires_user_notice: bool
    user_notice: str | None
    reasons: tuple[str, ...]
    safe_for_source_retrieval: bool
    validation_status: Literal["machine_checked", "unreviewed"]
    evidence: Annotated[tuple[Citation, ...], Field(min_length=1)]


class ReadingContext(ContractModel):
    mode: Literal["wasl", "waqf"]
    # None means unknown, never an assumed reading boundary.
    preceding: QalounReference | None = None
    following: QalounReference | None = None
    stop_after_word: PositiveInt | None = None


class TextAnchor(ContractModel):
    reference: QalounReference
    ayah_sha256: Sha256
    start_codepoint: Annotated[int, Field(strict=True, ge=0)]
    end_codepoint: PositiveInt
    word_index: PositiveInt

    @model_validator(mode="after")
    def ordered_offsets(self) -> "TextAnchor":
        if self.end_codepoint <= self.start_codepoint:
            raise ValueError("Anchor must have a nonempty half-open codepoint range")
        return self


class TajwidAnnotation(ContractModel):
    annotation_id: NonEmpty
    version: NonEmpty
    rule_id: NonEmpty
    rule_version: NonEmpty
    anchor: TextAnchor
    reading_context: ReadingContext
    detector_version: NonEmpty | None = None
    status: Literal["candidate", "scholarly_verified", "rejected"]
    evidence: Annotated[tuple[Citation, ...], Field(min_length=1)]
    validation_record_ids: tuple[NonEmpty, ...] = ()

    @model_validator(mode="after")
    def review_required(self) -> "TajwidAnnotation":
        if self.status == "scholarly_verified" and not self.validation_record_ids:
            raise ValueError("Verified annotations require scholarly validation records")
        return self


class Success[T](ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["ok"] = "ok"
    data: T
    provenance: Annotated[tuple[Provenance, ...], Field(min_length=1)]
    validation_status: ValidationStatus
    warnings: tuple[str, ...] = ()


class DomainError(ContractModel):
    code: Literal[
        "INVALID_REFERENCE",
        "DATA_UNAVAILABLE",
        "INTEGRITY_FAILURE",
        "AMBIGUOUS_MAPPING",
        "UNSUPPORTED_CORRESPONDENCE",
        "NOT_FOUND",
        "UNVERIFIED_EVIDENCE",
        "UNSUPPORTED_CONTEXT",
        "INCOMPATIBLE_RIWAYA",
        "SCHEMA_MISMATCH",
        "UNSUPPORTED_VERSION",
        "UNSUPPORTED_CAPABILITY",
    ]
    message: str
    retryable: bool = False


class Failure(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["error"] = "error"
    error: DomainError
