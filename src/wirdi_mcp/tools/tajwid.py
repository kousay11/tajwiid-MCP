"""Local Tajwid tool surface.

The handlers deliberately fail closed until reviewed rule data and a detector
are added. No external MCP client or scholarly fallback is involved.
"""

from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations

from wirdi_mcp.domain.models import Failure, NonEmpty, PassageSelection, ReadingContext
from wirdi_mcp.tools.contracts import (
    AnalysisToolResponse,
    ExplanationToolResponse,
    RuleToolResponse,
)
from wirdi_mcp.tools.quran import tool_result


def _unavailable() -> CallToolResult:
    return tool_result(
        Failure(
            error={
                "code": "UNSUPPORTED_CAPABILITY",
                "message": "Local Tajwid rules and detectors are not loaded yet",
            }
        )
    )


def register_tajwid_tools(server: MCPServer) -> None:
    annotations = ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )

    @server.tool(annotations=annotations)
    async def get_tajwid_rule(
        rule_id: NonEmpty,
        version: NonEmpty,
    ) -> Annotated[CallToolResult, RuleToolResponse]:
        """Read a reviewed local Tajwid rule; no external source is queried."""
        return _unavailable()

    @server.tool(annotations=annotations)
    async def analyze_qaloun_tajwid(
        selection: PassageSelection,
        reading_context: ReadingContext,
        rule_ids: tuple[NonEmpty, ...] = (),
        include_candidates: bool = False,
    ) -> Annotated[CallToolResult, AnalysisToolResponse]:
        """Analyze a local Qaloun passage when a reviewed detector is available."""
        return _unavailable()

    @server.tool(annotations=annotations)
    async def get_tajwid_explanation(
        annotation_id: NonEmpty,
        annotation_version: NonEmpty,
        language: Literal["ar"] = "ar",
    ) -> Annotated[CallToolResult, ExplanationToolResponse]:
        """Read a locally reviewed explanation without a network fallback."""
        return _unavailable()
