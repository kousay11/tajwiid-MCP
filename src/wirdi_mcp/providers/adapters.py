"""Typed adapters for demonstrated scholarly searches; no generic passthrough."""

import hashlib
import re
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from wirdi_mcp.providers.base import SearchBatch
from wirdi_mcp.providers.models import (
    ExternalHit,
    GatewayError,
    ProviderCitation,
    ProviderReference,
    SearchRequest,
    canonical_hash,
)
from wirdi_mcp.providers.transport import Channel


class UpstreamModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class QuranCitation(UpstreamModel):
    edition_id: str = Field(min_length=1)
    edition_name: str = Field(min_length=1)
    author: str = Field(min_length=1)


class QuranHit(UpstreamModel):
    ayah_key: str
    surah: int = Field(strict=True, ge=1, le=114)
    ayah: int = Field(strict=True, ge=1, le=286)
    tafsir_text: str = Field(min_length=1)
    citation: QuranCitation
    citation_url: str | None = None
    passage_ayah_range: str | None = None
    ayah_keys: list[str] | None = None


class TafsirHit(UpstreamModel):
    surah: int = Field(strict=True, ge=1, le=114)
    ayah: int = Field(strict=True, ge=1, le=286)
    tafsir_excerpt: str = Field(min_length=1)
    tafsir_excerpt_raw: str | None = Field(default=None, min_length=1)
    source_attribution: str = Field(min_length=1)


def parse_ref(text: str) -> set[tuple[int, int]]:
    match = re.fullmatch(r"([1-9]\d{0,2}):([1-9]\d{0,2})(?:-([1-9]\d{0,2}))?", text)
    if not match:
        raise GatewayError("SCHEMA_MISMATCH", "Provider reference is missing or malformed")
    surah, lo, hi = int(match[1]), int(match[2]), int(match[3] or match[2])
    if not 1 <= surah <= 114 or not 1 <= lo <= hi <= 286:
        raise GatewayError("SCHEMA_MISMATCH", "Provider reference is out of bounds")
    return {(surah, n) for n in range(lo, hi + 1)}


def reference(profile, refs):
    ordered = sorted(refs)
    if not ordered or len({s for s, _ in ordered}) != 1:
        raise GatewayError("SCHEMA_MISMATCH", "Provider passage is not a single contiguous range")
    surah, lo = ordered[0]
    hi = ordered[-1][1]
    if ordered != [(surah, n) for n in range(lo, hi + 1)]:
        raise GatewayError("SCHEMA_MISMATCH", "Provider passage contains unchecked gaps")
    return ProviderReference(source_id=profile["source_id"], surah=surah, from_ayah=lo, to_ayah=hi)


def hit(profile, tool, excerpt, ref, citation, metadata, response_sha):
    return ExternalHit(
        hit_id=canonical_hash(
            [profile["provider_id"], citation.work_id, ref.model_dump(), excerpt]
        ),
        provider_id=profile["provider_id"],
        provider_tool=tool,
        excerpt=excerpt,
        excerpt_sha256=hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        source_reference=ref,
        citation=citation,
        original_metadata=metadata,
        response_sha256=response_sha,
        retrieved_at=datetime.now(UTC),
        compatibility="unknown",
    )


class QuranMcpAdapter:
    async def prerequisite(self, channel):
        # Guidance is data, never executable service policy or LLM instructions.
        await channel.call("fetch_grounding_rules", {}, plain_text=True)

    async def source_texts(self, channel: Channel, refs: set[tuple[int, int]]) -> dict:
        result, _ = await channel.call(
            "fetch_quran",
            {
                "ayahs": [f"{s}:{n}" for s, n in sorted(refs)],
                "editions": "ar-uthmani-hafs",
            },
        )
        if result.get("pagination", {}).get("has_more"):
            raise GatewayError("UNVERIFIED_EVIDENCE", "Provider boundary response is incomplete")
        rows = result["results"].get("ar-uthmani-hafs")
        if not isinstance(rows, list):
            raise GatewayError(
                "UNVERIFIED_EVIDENCE", "Requested provider Quran edition is unavailable"
            )
        texts = {}
        for row in rows:
            keys = parse_ref(row["ayah"])
            if len(keys) != 1 or not isinstance(row["text"], str) or not row["text"]:
                raise GatewayError("SCHEMA_MISMATCH", "Provider verse text has invalid boundaries")
            key = next(iter(keys))
            if key in texts:
                raise GatewayError("SCHEMA_MISMATCH", "Provider returned duplicate verse records")
            texts[key] = row["text"]
        return texts

    async def search(self, channel: Channel, request: SearchRequest, refs) -> SearchBatch:
        args = {"query": request.query, "editions": "ar-saadi", "include_ayah_text": False}
        if refs is not None:
            args["ayahs"] = [f"{s}:{n}" for s, n in sorted(refs)]
        data, sha = await channel.call("search_tafsir", args)
        rows = TypeAdapter(list[QuranHit]).validate_python(data["results"])
        hits, excluded = [], 0
        for row in rows:
            if row.citation.edition_id != "ar-saadi":
                raise GatewayError(
                    "UNVERIFIED_EVIDENCE", "Provider returned an unrequested scholarly work"
                )
            covered = parse_ref(row.ayah_key)
            if row.ayah_keys:
                explicit = set().union(*(parse_ref(k) for k in row.ayah_keys))
                if explicit != covered:
                    raise GatewayError("SCHEMA_MISMATCH", "Provider passage references disagree")
            if (row.surah, row.ayah) != min(covered):
                raise GatewayError(
                    "SCHEMA_MISMATCH", "Provider row and passage identities disagree"
                )
            if row.passage_ayah_range:
                covered |= parse_ref(row.passage_ayah_range)
            ref = reference(channel.profile, covered)
            if refs is not None and not covered <= refs:
                excluded += 1
                continue
            citation = ProviderCitation(
                work_id=row.citation.edition_id,
                title=row.citation.edition_name,
                author=row.citation.author,
                locator=row.passage_ayah_range or row.ayah_key,
                uri=row.citation_url,
                license_notice=channel.profile["license_notice"],
            )
            hits.append(
                hit(
                    channel.profile,
                    "search_tafsir",
                    row.tafsir_text,
                    ref,
                    citation,
                    row.model_dump(exclude={"tafsir_text", "ayah_text"}),
                    sha,
                )
            )
        partial = bool(
            data.get("pagination", {}).get("has_more") or len(hits) > request.limit or excluded
        )
        warnings = (
            ("Provider search is a bounded first page; no completeness claim.",) if partial else ()
        )
        return SearchBatch(tuple(hits[: request.limit]), partial, warnings)


class TafsirMcpAdapter:
    async def source_texts(self, channel: Channel, refs: set[tuple[int, int]]) -> dict:
        texts = {}
        for s, n in sorted(refs):
            data, _ = await channel.call("fetch_ayah", {"surah": s, "ayah": n, "include": []})
            if type(data.get("surah")) is not int or type(data.get("ayah")) is not int:
                raise GatewayError("SCHEMA_MISMATCH", "Provider verse identity is invalid")
            if (data["surah"], data["ayah"]) != (s, n) or not isinstance(data.get("text"), str):
                raise GatewayError("SCHEMA_MISMATCH", "Provider returned another verse or no text")
            texts[s, n] = data["text"]
        return texts

    async def search(self, channel: Channel, request: SearchRequest, refs) -> SearchBatch:
        metadata, _ = await channel.call("list_tafsir_sources", {})
        works = [x for x in metadata["items"] if x.get("slug") == "saadi"]
        if len(works) != 1 or not works[0].get("name") or not works[0].get("attribution"):
            raise GatewayError(
                "UNVERIFIED_EVIDENCE", "Provider scholarly attribution is unavailable"
            )
        args = {"query": request.query, "source": "saadi", "limit": request.limit}
        if refs is not None:
            args["surah"] = min(refs)[0]
        data, sha = await channel.call("search_in_tafsir", args)
        if isinstance(data, dict):
            data = data["result"]
        rows = TypeAdapter(list[TafsirHit]).validate_python(data)
        hits, excluded = [], 0
        for row in rows:
            if row.source_attribution != works[0]["attribution"]:
                raise GatewayError(
                    "UNVERIFIED_EVIDENCE", "Provider search and source attribution disagree"
                )
            key = row.surah, row.ayah
            if refs is not None and key not in refs:
                excluded += 1
                continue
            ref = reference(channel.profile, {key})
            citation = ProviderCitation(
                work_id="saadi",
                title=works[0]["name"],
                attribution=row.source_attribution,
                locator=f"{row.surah}:{row.ayah}",
                license_notice=channel.profile["license_notice"],
            )
            excerpt = (
                row.tafsir_excerpt_raw if row.tafsir_excerpt_raw is not None else row.tafsir_excerpt
            )
            metadata = {
                "source_catalog_entry": works[0],
                **row.model_dump(
                    exclude={
                        "tafsir_excerpt",
                        "tafsir_excerpt_raw",
                        "tafsir_excerpt_clean",
                        "_display",
                    }
                ),
            }
            hits.append(
                hit(channel.profile, "search_in_tafsir", excerpt, ref, citation, metadata, sha)
            )
        warnings = ("Provider excerpts may be truncated; publication edition remains unverified.",)
        return SearchBatch(
            tuple(hits[: request.limit]),
            bool(refs or excluded or len(rows) >= request.limit),
            warnings,
        )


ADAPTERS = {"quran_mcp": QuranMcpAdapter, "tafsir_mcp": TafsirMcpAdapter}


def invalid_payload(exc):
    if isinstance(exc, (ValidationError, KeyError, TypeError, ValueError, AttributeError)):
        return GatewayError(
            "SCHEMA_MISMATCH", "Provider payload is malformed or missing required fields"
        )
    return exc
