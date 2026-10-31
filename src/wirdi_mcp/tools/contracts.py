"""Implemented Quran tool schemas and unregistered future knowledge contracts."""

from typing import Literal

from pydantic import ConfigDict, RootModel

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


class AnalyzeInput(GetPassageInput):
    reading_context: ReadingContext
    rule_ids: tuple[NonEmpty, ...] = ()
    include_candidates: bool = False


class Analysis(ContractModel):
    annotations: tuple[TajwidAnnotation, ...]
    coverage: Literal["partial", "complete_for_requested_rules", "unsupported"]
    evaluated_rule_versions: tuple[NonEmpty, ...]
    limitations: tuple[str, ...]


class GetExplanationInput(ContractModel):
    annotation_id: NonEmpty
    annotation_version: NonEmpty
    language: Literal["ar"] = "ar"


class Explanation(ContractModel):
    annotation: TajwidAnnotation
    rule: TajwidRule
    explanation_ar: str
    template_version: NonEmpty


class RuleToolResponse(RootModel[Success[TajwidRule] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class AnalysisToolResponse(RootModel[Success[Analysis] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


class ExplanationToolResponse(RootModel[Success[Explanation] | Failure]):
    model_config = ConfigDict(json_schema_extra={"type": "object"})


# Input class, result type, earliest phase. Contract presence does not imply availability.
TOOL_CONTRACTS = {
    "get_qaloun_passage": (GetPassageInput, Success[Passage] | Failure, 2),
    "resolve_source_mapping": (ResolveMappingInput, Success[SourceMapping] | Failure, 2),
    "get_tajwid_rule": (GetRuleInput, Success[TajwidRule] | Failure, 4),
    "analyze_qaloun_tajwid": (AnalyzeInput, Success[Analysis] | Failure, 5),
    "get_tajwid_explanation": (GetExplanationInput, Success[Explanation] | Failure, 5),
}
