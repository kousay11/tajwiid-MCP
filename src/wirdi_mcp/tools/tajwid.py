"""Local Tajwid tool surface.

Rules, candidates and summaries come only from checksum-pinned local data. Every failure is
a typed envelope; none leaks a path, a source text or a raw exception message.
"""

import asyncio
from collections.abc import Callable
from typing import Annotated

from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations
from pydantic import ValidationError

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.domain.models import (
    Failure,
    NonEmpty,
    PassageSelection,
    Provenance,
    ReadingContext,
    Success,
)
from wirdi_mcp.knowledge.pages import PageStore
from wirdi_mcp.quran.source import TARIQ_WARNING, PublicSourceRepository
from wirdi_mcp.tajwid.letters import normalize_letter, properties
from wirdi_mcp.tajwid.service import TajwidService
from wirdi_mcp.tools.contracts import (
    AnalysisToolResponse,
    AppPageInput,
    AppPageToolResponse,
    GetLetterPropertiesInput,
    GetSourcePageInput,
    LetterProperties,
    LetterPropertiesData,
    LetterPropertiesResponse,
    ListRulesInput,
    ReadingCombinationsInput,
    ReadingCombinationsResponse,
    RuleListResponse,
    RuleToolResponse,
    SearchSourcePagesInput,
    SourcePageHit,
    SourcePageHitsResponse,
    SourcePageRecord,
    SourcePages,
    SourcePagesResponse,
    SummaryInput,
    SummaryToolResponse,
)
from wirdi_mcp.tools.quran import tool_result

CANDIDATE_WARNINGS = (
    TARIQ_WARNING,
    "All Tajwid annotations are unreviewed candidates; none is scholarly verified.",
)


def _guard(call: Callable[[], Success | Failure]) -> CallToolResult:
    try:
        return tool_result(call())
    except KnowledgeError as exc:
        return tool_result(Failure(error=exc.error))
    except ValidationError:
        return tool_result(
            Failure(error={"code": "INVALID_REFERENCE", "message": "Invalid request parameters"})
        )
    except Exception:  # noqa: BLE001 - a tool must never crash the server or echo internals
        return tool_result(
            Failure(
                error={"code": "DATA_UNAVAILABLE", "message": "The request could not be served"}
            )
        )


def register_tajwid_tools(
    server: MCPServer,
    repository: PublicSourceRepository,
    service: TajwidService,
    pages: PageStore,
) -> None:
    annotations = ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )

    def corpus_provenance() -> Provenance:
        return repository.provenance("qalun", "Canonical Qaloun source records")

    @server.tool(annotations=annotations)
    async def get_tajwid_rule(
        rule_id: NonEmpty,
        version: NonEmpty,
    ) -> Annotated[CallToolResult, RuleToolResponse]:
        """Read a local Tajwid rule record with its page-level citations (unreviewed)."""

        def run():
            rule = service.get_rule(rule_id, version)
            return Success(
                data=rule,
                provenance=(service.rules_provenance(),),
                validation_status=rule.validation_status,
                warnings=(
                    "Rule text is a paraphrase of cited pages and is not scholarly reviewed.",
                ),
            )

        return await asyncio.to_thread(_guard, run)

    @server.tool(annotations=annotations)
    async def list_tajwid_rules(
        family: NonEmpty | None = None,
    ) -> Annotated[CallToolResult, RuleListResponse]:
        """List the available local rules and whether a detector exists for each."""
        request = ListRulesInput(family=family)

        def run():
            return Success(
                data=service.list_rules(request.family),
                provenance=(service.rules_provenance(),),
                validation_status="unreviewed",
            )

        return await asyncio.to_thread(_guard, run)

    @server.tool(annotations=annotations)
    async def analyze_qaloun_tajwid(
        selection: PassageSelection,
        reading_context: ReadingContext,
        rule_ids: tuple[NonEmpty, ...] = (),
        include_candidates: bool = True,
        families: tuple[NonEmpty, ...] = (),
        limit: int = 100,
        offset: int = 0,
    ) -> Annotated[CallToolResult, AnalysisToolResponse]:
        """Candidate Tajwid occurrences for 1 to 100 Qaloun ayat, paged, each with its citations."""

        def run():
            from wirdi_mcp.tools.contracts import AnalyzeInput

            request = AnalyzeInput(
                selection=selection,
                reading_context=reading_context,
                rule_ids=rule_ids,
                families=families,
                include_candidates=include_candidates,
                limit=limit,
                offset=offset,
            )
            analysis = service.analyze(
                request.selection,
                request.reading_context,
                request.rule_ids,
                request.families,
                request.include_candidates,
                request.limit,
                request.offset,
            )
            return Success(
                data=analysis,
                provenance=(corpus_provenance(), service.rules_provenance()),
                validation_status="unreviewed",
                warnings=CANDIDATE_WARNINGS,
            )

        return await asyncio.to_thread(_guard, run)

    @server.tool(annotations=annotations)
    async def list_reading_combinations(
        selection: PassageSelection,
        reading_context: ReadingContext,
        max_combinations: int = 200,
    ) -> Annotated[CallToolResult, ReadingCombinationsResponse]:
        """Which readings of the madds may be taken together in each ayah (the book's tables)."""

        def run():
            request = ReadingCombinationsInput(
                selection=selection,
                reading_context=reading_context,
                max_combinations=max_combinations,
            )
            data = service.reading_combinations(
                request.selection, request.reading_context, request.max_combinations
            )
            return Success(
                data=data,
                provenance=(corpus_provenance(), service.rules_provenance()),
                validation_status="unreviewed",
                warnings=CANDIDATE_WARNINGS,
            )

        return await asyncio.to_thread(_guard, run)

    @server.tool(annotations=annotations)
    async def summarize_tajwid(
        surah: int,
        reading_context: ReadingContext,
        start_ayah: int | None = None,
        end_ayah: int | None = None,
        rule_ids: tuple[NonEmpty, ...] = (),
        families: tuple[NonEmpty, ...] = (),
        limit: int = 50,
        offset: int = 0,
    ) -> Annotated[CallToolResult, SummaryToolResponse]:
        """Per-rule candidate counts for a surah or an ayah range, with per-ayah counts (paged)."""

        def run():
            request = SummaryInput(
                surah=surah,
                start_ayah=start_ayah,
                end_ayah=end_ayah,
                reading_context=reading_context,
                rule_ids=rule_ids,
                families=families,
                limit=limit,
                offset=offset,
            )
            summary = service.summarize(
                request.surah,
                request.start_ayah,
                request.end_ayah,
                request.reading_context,
                request.rule_ids,
                request.families,
                request.limit,
                request.offset,
            )
            return Success(
                data=summary,
                provenance=(corpus_provenance(), service.rules_provenance()),
                validation_status="unreviewed",
                warnings=CANDIDATE_WARNINGS,
            )

        return await asyncio.to_thread(_guard, run)

    @server.tool(annotations=annotations)
    async def analyze_app_page(
        page: int,
        reading_context: ReadingContext,
        rule_ids: tuple[NonEmpty, ...] = (),
        families: tuple[NonEmpty, ...] = (),
        limit: int = 100,
        offset: int = 0,
    ) -> Annotated[CallToolResult, AppPageToolResponse]:
        """Candidates for the ayat that begin on a page of the verified 559-page Qaloun layout."""

        def run():
            request = AppPageInput(
                page=page,
                reading_context=reading_context,
                rule_ids=rule_ids,
                families=families,
                limit=limit,
                offset=offset,
            )
            result = service.analyze_page(
                request.page,
                request.reading_context,
                request.rule_ids,
                request.families,
                request.limit,
                request.offset,
            )
            return Success(
                data=result,
                provenance=(corpus_provenance(), service.rules_provenance()),
                validation_status="unreviewed",
                warnings=CANDIDATE_WARNINGS,
            )

        return await asyncio.to_thread(_guard, run)

    @server.tool(annotations=annotations)
    async def get_source_page(
        edition_id: NonEmpty,
        page_start: int,
        page_end: int,
    ) -> Annotated[CallToolResult, SourcePagesResponse]:
        """Read 1 to 5 pages of a locally placed source book (printed page numbers)."""

        def run():
            request = GetSourcePageInput(
                edition_id=edition_id, page_start=page_start, page_end=page_end
            )
            found = pages.get_pages(request.edition_id, request.page_start, request.page_end)
            return Success(
                data=SourcePages(
                    pages=tuple(
                        SourcePageRecord(
                            edition_id=p.edition_id,
                            printed_page=p.printed_page,
                            pdf_page=p.pdf_page,
                            text=p.text,
                            text_sha256=p.text_sha256,
                            text_quality=p.text_quality,
                        )
                        for p in found
                    )
                ),
                provenance=(service.rules_provenance(),),
                validation_status="unreviewed",
                warnings=(
                    "Local copy of a source with unknown licence; extracted text is unreviewed.",
                ),
            )

        return await asyncio.to_thread(_guard, run)

    @server.tool(annotations=annotations)
    async def search_source_pages(
        query: str,
        edition_ids: tuple[NonEmpty, ...],
        limit: int = 20,
    ) -> Annotated[CallToolResult, SourcePageHitsResponse]:
        """Literal Arabic search over locally placed source pages; returns page hits only."""

        def run():
            request = SearchSourcePagesInput(query=query, edition_ids=edition_ids, limit=limit)
            found = pages.search(request.query, request.edition_ids, request.limit)
            from wirdi_mcp.tools.contracts import SourcePageHits

            return Success(
                data=SourcePageHits(
                    hits=tuple(
                        SourcePageHit(
                            edition_id=page.edition_id,
                            printed_page=page.printed_page,
                            pdf_page=page.pdf_page,
                            match_count=count,
                            snippet=snippet,
                        )
                        for page, count, snippet in found
                    )
                ),
                provenance=(service.rules_provenance(),),
                validation_status="unreviewed",
                warnings=(
                    "Matching is lossy: marks and letter variants are folded, and the extractor's "
                    "inverted lam-alef order is tolerated.",
                ),
            )

        return await asyncio.to_thread(_guard, run)

    @server.tool(annotations=annotations)
    async def get_letter_properties(
        letters: tuple[NonEmpty, ...],
    ) -> Annotated[CallToolResult, LetterPropertiesResponse]:
        """Place of articulation and characteristics of 1 to 29 Arabic letters (Book A pp.40-45)."""

        def run():
            request = GetLetterPropertiesInput(letters=letters)
            found = []
            for given in request.letters:
                base = normalize_letter(given) if len(given) == 1 else None
                if base is None:
                    raise KnowledgeError(
                        "INVALID_REFERENCE", "Each entry must be one base Arabic letter"
                    )
                data = properties(base)
                found.append(
                    LetterProperties(
                        letter=base,
                        makhraj_region=data.region,
                        makhraj_place=data.place,
                        paired_characteristics=data.paired,
                        other_characteristics=data.other,
                    )
                )
            return Success(
                data=LetterPropertiesData(
                    letters=tuple(found),
                    source_pages=("book-a-2010 p.40", "p.41", "p.42", "p.43", "p.44", "p.45"),
                    limitations=(
                        "Static tables from the cited pages; hamza and alef are counted "
                        "separately (29 letters). Not scholarly reviewed.",
                    ),
                ),
                provenance=(service.rules_provenance(),),
                validation_status="unreviewed",
                warnings=("Letter data is a paraphrase of Book A and is not scholarly reviewed.",),
            )

        return await asyncio.to_thread(_guard, run)
