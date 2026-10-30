"""Provider contracts: external evidence never becomes canonical Quran content."""

import hashlib
import json
from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, RootModel, model_validator

from wirdi_mcp.domain.models import ContractModel, NonEmpty, PassageSelection, Sha256

ProviderId = Literal["quran_mcp", "tafsir_mcp", "quran_search_mcp"]


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def signature_schema(value):
    """Ignore documentation-only schema metadata; preserve validation and defaults."""
    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if k in {"description", "title", "examples", "$schema"}:
                continue
            if k in {"properties", "$defs", "definitions", "patternProperties"}:
                result[k] = {name: signature_schema(schema) for name, schema in v.items()}
            elif k in {"default", "const", "enum"}:
                result[k] = v
            else:
                result[k] = signature_schema(v)
        return result
    if isinstance(value, list):
        return [signature_schema(v) for v in value]
    return value


class ProviderIssue(ContractModel):
    provider_id: ProviderId | None = None
    code: Literal[
        "INVALID_CONFIG",
        "NOT_FOUND",
        "PROVIDER_UNAVAILABLE",
        "PROVIDER_TIMEOUT",
        "AUTHENTICATION_FAILED",
        "RATE_LIMITED",
        "PROVIDER_CALL_FAILED",
        "SCHEMA_MISMATCH",
        "RESPONSE_TOO_LARGE",
        "UNVERIFIED_EVIDENCE",
        "UNSUPPORTED_CAPABILITY",
        "INVALID_REFERENCE",
        "UNSUPPORTED_VERSION",
        "UNSUPPORTED_CONTEXT",
        "DATA_UNAVAILABLE",
        "INTEGRITY_FAILURE",
        "AMBIGUOUS_MAPPING",
        "INCOMPATIBLE_RIWAYA",
    ]
    message: str
    retryable: bool = False


class GatewayError(Exception):
    def __init__(self, code: str, message: str, provider_id=None, retryable=False):
        self.issue = ProviderIssue(
            code=code,
            message=message,
            provider_id=provider_id,
            retryable=retryable,
        )
        super().__init__(message)


class Capability(ContractModel):
    provider_id: ProviderId
    tool_name: str
    input_schema: dict
    output_schema: dict | None
    signature_sha256: Sha256
    admitted: bool
    evidence_level: Literal["runtime_discovered", "call_tested"]
    categories: tuple[str, ...]


class ProviderState(ContractModel):
    provider_id: ProviderId
    enabled: bool
    status: Literal["disabled", "not_discovered", "ready", "unavailable"]
    source_id: str
    dataset_version: str | None = None
    tools: tuple[Capability, ...] = ()
    observed_at: datetime | None = None
    issues: tuple[ProviderIssue, ...] = ()


class CapabilitiesResult(ContractModel):
    providers: tuple[ProviderState, ...]


class SourceIdentity(ContractModel):
    """Explicit local mapping target plus each permitted provider's source namespace."""

    corpus_id: NonEmpty
    corpus_version: NonEmpty
    numbering_system: NonEmpty
    provider_sources: dict[ProviderId, NonEmpty]


class SearchRequest(ContractModel):
    query: Annotated[str, Field(min_length=1, max_length=1000)]
    category: Literal["tafsir"] = "tafsir"
    work_id: Literal["saadi"] = "saadi"
    limit: Annotated[int, Field(strict=True, ge=1, le=20)] = 10
    provider_ids: tuple[ProviderId, ...] = ()
    selection: PassageSelection | None = None
    source_identity: SourceIdentity | None = None

    @model_validator(mode="after")
    def explicit_scope(self):
        if (self.selection is None) != (self.source_identity is None):
            raise ValueError(
                "Passage selection and explicit source identity must be provided together"
            )
        if not self.query.strip() or len(set(self.provider_ids)) != len(self.provider_ids):
            raise ValueError("Query must be nonblank and provider IDs unique")
        return self


class ProviderReference(ContractModel):
    source_id: str
    dataset_version: str | None = None
    numbering_system: Literal["provider_declared_hafs_style"] = "provider_declared_hafs_style"
    surah: Annotated[int, Field(strict=True, ge=1, le=114)]
    from_ayah: Annotated[int, Field(strict=True, ge=1)]
    to_ayah: Annotated[int, Field(strict=True, ge=1)]

    @model_validator(mode="after")
    def ordered(self):
        if self.to_ayah < self.from_ayah or self.to_ayah - self.from_ayah >= 300:
            raise ValueError("Invalid provider passage bounds")
        return self


class ProviderCitation(ContractModel):
    work_id: str
    title: Annotated[str, Field(min_length=1)]
    author: str | None = None
    attribution: str | None = None
    publication: str | None = None
    locator: str
    uri: str | None = None
    license_notice: str
    validation_status: Literal["provider_attributed_edition_unverified"] = (
        "provider_attributed_edition_unverified"
    )


class ExternalHit(ContractModel):
    hit_id: Sha256
    provider_id: ProviderId
    provider_tool: str
    kind: Literal["source_excerpt"] = "source_excerpt"
    excerpt: str
    excerpt_sha256: Sha256
    source_reference: ProviderReference
    citation: ProviderCitation
    original_metadata: dict
    response_sha256: Sha256
    retrieved_at: datetime
    compatibility: Literal["unknown", "mapped_boundaries_checked"]
    mapping_sha256: Sha256 | None = None
    validation_status: Literal["unreviewed"] = "unreviewed"


class ProviderAttempt(ContractModel):
    provider_id: ProviderId
    outcome: Literal["success", "empty", "failed"]


class SearchResult(ContractModel):
    hits: tuple[ExternalHit, ...]
    partial: bool
    attempts: tuple[ProviderAttempt, ...]
    issues: tuple[ProviderIssue, ...]
    warnings: tuple[str, ...]
    mapping_status: str | None = None


class GatewaySuccess[T](ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["ok"] = "ok"
    data: T


class GatewayFailure(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["error"] = "error"
    error: ProviderIssue
    issues: tuple[ProviderIssue, ...] = ()


class CapabilitiesResponse(RootModel[GatewaySuccess[CapabilitiesResult] | GatewayFailure]):
    pass


class SearchResponse(RootModel[GatewaySuccess[SearchResult] | GatewayFailure]):
    pass
