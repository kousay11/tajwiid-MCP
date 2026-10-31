"""No private data, environment values, paths, or network checks."""

from typing import Literal

from wirdi_mcp import __version__
from wirdi_mcp.domain.models import ContractModel


class HealthReport(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["foundation_ready"] = "foundation_ready"
    service_version: str = __version__
    available_tools: tuple[str, ...] = (
        "health_check",
        "get_qaloun_passage",
        "resolve_source_mapping",
        "get_tajwid_rule",
        "list_tajwid_rules",
        "analyze_qaloun_tajwid",
        "summarize_tajwid",
        "analyze_app_page",
        "get_source_page",
        "search_source_pages",
        "get_letter_properties",
    )
    quran_data: Literal["not_configured", "configured_unchecked"] = "not_configured"
    mapping: Literal["not_configured", "configured_unchecked"] = "not_configured"
    quran_source: Literal["bundled", "external", "none"] = "none"
    tajwid_analysis: Literal["candidates_only_unreviewed"] = "candidates_only_unreviewed"
    validation_status: Literal["not_applicable"] = "not_applicable"


def health_check() -> HealthReport:
    """Report foundation readiness and explicitly unavailable knowledge capabilities."""
    return HealthReport()
