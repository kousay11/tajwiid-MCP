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
        "get_provider_capabilities",
        "search_scholarly_sources",
    )
    quran_data: Literal["not_configured", "configured_unchecked"] = "not_configured"
    mapping: Literal["not_configured", "configured_unchecked"] = "not_configured"
    external_providers: Literal["disabled", "configured_unchecked"] = "disabled"
    tajwid_analysis: Literal["not_implemented"] = "not_implemented"
    validation_status: Literal["not_applicable"] = "not_applicable"


def health_check() -> HealthReport:
    """Report foundation readiness and explicitly unavailable knowledge capabilities."""
    return HealthReport()
