"""Implemented Quran tool schemas and unregistered future knowledge contracts."""

from typing import Annotated, Literal

from pydantic import ConfigDict, Field, RootModel

from wirdi_mcp.domain.models import (
    ContractModel,
    Failure,
    NonEmpty,
    Passage,
    PassageSelection,
    ReadingContext,
    SourceMapping,
    Success,
    TajwidAnnotation,
)
from wirdi_mcp.knowledge.models import TajwidRule


class GetPassageInput(ContractModel):
    selection: PassageSelection


class ResolveMappingInput(GetPassageInput):
    target_corpus_id: NonEmpty
    target_corpus_version: NonEmpty
    target_numbering_system: NonEmpty


class PassageToolResponse(RootModel[Success[Passage] | Failure]):
    """Object-shaped result union without the SDK's primitive-result wrapper."""

    model_config = ConfigDict(json_schema_extra={"type": "object"})


class MappingToolResponse(RootModel[Success[SourceMapping] | Failure]):
    """Object-shaped result union without the SDK's primitive-result wrapper."""

    model_config = ConfigDict(json_schema_extra={"type": "object"})


class GetRuleInput(ContractModel):
    rule_id: NonEmpty
    version: NonEmpty


MAX_PAGE_SIZE = 500
Limit = Annotated[int, Field(strict=True, ge=1, le=MAX_PAGE_SIZE)]
Offset = Annotated[int, Field(strict=True, ge=0, le=1_000_000)]
RuleIds = Annotated[tuple[NonEmpty, ...], Field(max_length=32)]


class AnalyzeInput(GetPassageInput):
    reading_context: ReadingContext
    rule_ids: RuleIds = ()
    families: RuleIds = ()
    # Candidates are the only kind that exists; False asks for reviewed annotations only.
    include_candidates: bool = True
    limit: Limit = 100
    offset: Offset = 0


class Analysis(ContractModel):
    annotations: tuple[TajwidAnnotation, ...]
    coverage: Literal["partial", "complete_for_requested_rules", "unsupported"]
    evaluated_rule_versions: tuple[NonEmpty, ...]
    limitations: tuple[str, ...]
    # Paging: `total` counts every occurrence of the requested rules in the selection.
    total: int = 0
    offset: int = 0
    next_offset: int | None = None
    rule_counts: dict[str, int] = {}
    # Positions a rule could not decide (missing context) and positions deliberately skipped.
    unresolved: dict[str, int] = {}
    skipped: dict[str, int] = {}


class AyahCounts(ContractModel):
    surah: int
    ayah: int
    counts: dict[str, int]


class SummaryInput(ContractModel):
    surah: Annotated[int, Field(strict=True, ge=1, le=114)]
    start_ayah: Annotated[int, Field(strict=True, ge=1)] | None = None
    end_ayah: Annotated[int, Field(strict=True, ge=1)] | None = None
    reading_context: ReadingContext
    rule_ids: RuleIds = ()
    families: RuleIds = ()
    limit: Annotated[int, Field(strict=True, ge=1, le=100)] = 50
    offset: Offset = 0


class TajwidSummary(ContractModel):
    surah: int
    start_ayah: int
    end_ayah: int
    rule_counts: dict[str, int]
    per_ayah: tuple[AyahCounts, ...]
    total_ayat: int
    offset: int
    next_offset: int | None
    evaluated_rule_versions: tuple[NonEmpty, ...]
    coverage: Literal["partial", "complete_for_requested_rules", "unsupported"]
    unresolved: dict[str, int]
    limitations: tuple[str, ...]


class ReadingCombinationsInput(GetPassageInput):
    reading_context: ReadingContext
    max_combinations: Annotated[int, Field(strict=True, ge=1, le=500)] = 200


class ReadingPosition(ContractModel):
    rule_id: NonEmpty
    kind: NonEmpty
    word_index: int
    start_codepoint: int
    end_codepoint: int
    hamza_vowel: Literal["fatha", "damma", "kasra"] | None = None


class AyahCombinations(ContractModel):
    surah: int
    ayah: int
    positions: tuple[ReadingPosition, ...]
    # One row per legal combination, one reading per position, in the book's order.
    combinations: tuple[tuple[NonEmpty, ...], ...]
    total: int
    truncated: bool
    basis: Literal["single_position", "book_listed", "pairwise_extension", "unconstrained"]
    notes: tuple[str, ...] = ()


class ReadingCombinations(ContractModel):
    ayat: tuple[AyahCombinations, ...]
    evaluated_rules: tuple[NonEmpty, ...]
    limitations: tuple[str, ...]


class AppPageInput(ContractModel):
    page: Annotated[int, Field(strict=True, ge=1, le=559)]
    reading_context: ReadingContext
    rule_ids: RuleIds = ()
    families: RuleIds = ()
    limit: Limit = 100
    offset: Offset = 0


class PageVerse(ContractModel):
    surah: int
    ayah: int
    page_start: int
    page_end: int


class AppPageAnalysis(ContractModel):
    page: int
    pagination_status: Literal["verified_against_edition"]
    verses: tuple[PageVerse, ...]
    # Whole ayat that began on an earlier page and run onto this one; not analysed here.
    continued_from_previous_page: tuple[PageVerse, ...]
    analysis: Analysis


class ListRulesInput(ContractModel):
    family: NonEmpty | None = None


class RuleSummary(ContractModel):
    rule_id: str
    version: str
    name_ar: str
    family: str
    detectability: Literal["A", "B", "C"]
    tariq: Literal["abu_nashit", "unspecified"]
    validation_status: str
    has_detector: bool


class RuleList(ContractModel):
    rules: tuple[RuleSummary, ...]


class GetSourcePageInput(ContractModel):
    edition_id: NonEmpty
    page_start: Annotated[int, Field(strict=True, ge=1, le=10_000)]
    page_end: Annotated[int, Field(strict=True, ge=1, le=10_000)]


class SourcePageRecord(ContractModel):
    edition_id: str
    printed_page: str
    pdf_page: int
    text: str
    text_sha256: str
    text_quality: str


class SourcePages(ContractModel):
    pages: tuple[SourcePageRecord, ...]


class SearchSourcePagesInput(ContractModel):
    query: Annotated[str, Field(min_length=2, max_length=80)]
    edition_ids: Annotated[tuple[NonEmpty, ...], Field(min_length=1, max_length=4)]
    limit: Annotated[int, Field(strict=True, ge=1, le=50)] = 20


class SourcePageHit(ContractModel):
    edition_id: str
    printed_page: str
    pdf_page: int
    match_count: int
    snippet: str  # normalized (lossy) search form, not source text


class SourcePageHits(ContractModel):
    hits: tuple[SourcePageHit, ...]


class ReadingCombinationsResponse(RootModel[Success[ReadingCombinations] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class RuleListResponse(RootModel[Success[RuleList] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class SummaryToolResponse(RootModel[Success[TajwidSummary] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class AppPageToolResponse(RootModel[Success[AppPageAnalysis] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class SourcePagesResponse(RootModel[Success[SourcePages] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class SourcePageHitsResponse(RootModel[Success[SourcePageHits] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class RuleToolResponse(RootModel[Success[TajwidRule] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class AnalysisToolResponse(RootModel[Success[Analysis] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class GetLetterPropertiesInput(ContractModel):
    letters: Annotated[tuple[NonEmpty, ...], Field(min_length=1, max_length=29)]


class LetterProperties(ContractModel):
    letter: NonEmpty
    makhraj_region: NonEmpty
    makhraj_place: NonEmpty
    # one characteristic from each of the five opposed pairs, in the book's order
    paired_characteristics: tuple[NonEmpty, ...]
    other_characteristics: tuple[NonEmpty, ...]


class LetterPropertiesData(ContractModel):
    letters: tuple[LetterProperties, ...]
    source_pages: tuple[NonEmpty, ...]
    limitations: tuple[NonEmpty, ...]


class LetterPropertiesResponse(RootModel[Success[LetterPropertiesData] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


# Input class, result type, earliest phase. Contract presence does not imply availability.
TOOL_CONTRACTS = {
    "get_qaloun_passage": (GetPassageInput, Success[Passage] | Failure, 2),
    "resolve_source_mapping": (ResolveMappingInput, Success[SourceMapping] | Failure, 2),
    "get_tajwid_rule": (GetRuleInput, Success[TajwidRule] | Failure, 4),
    "list_tajwid_rules": (ListRulesInput, Success[RuleList] | Failure, 4),
    "analyze_qaloun_tajwid": (AnalyzeInput, Success[Analysis] | Failure, 5),
    "summarize_tajwid": (SummaryInput, Success[TajwidSummary] | Failure, 5),
    "analyze_app_page": (AppPageInput, Success[AppPageAnalysis] | Failure, 5),
    "list_reading_combinations": (
        ReadingCombinationsInput,
        Success[ReadingCombinations] | Failure,
        5,
    ),
    "get_source_page": (GetSourcePageInput, Success[SourcePages] | Failure, 4),
    "search_source_pages": (SearchSourcePagesInput, Success[SourcePageHits] | Failure, 4),
    "get_letter_properties": (GetLetterPropertiesInput, Success[LetterPropertiesData] | Failure, 4),
}
