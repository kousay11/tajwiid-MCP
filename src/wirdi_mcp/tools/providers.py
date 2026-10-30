"""Versioned provider tools. No raw external tool forwarding or user-data access."""

from typing import Annotated

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from wirdi_mcp.providers.gateway import ProviderGateway
from wirdi_mcp.providers.models import (
    CapabilitiesResponse,
    GatewayError,
    GatewayFailure,
    GatewaySuccess,
    ProviderId,
    SearchRequest,
    SearchResponse,
)


def result(payload):
    return CallToolResult(
        is_error=isinstance(payload, GatewayFailure),
        structured_content=payload.model_dump(mode="json"),
        content=[TextContent(type="text", text=payload.model_dump_json())],
    )


def register_provider_tools(server: MCPServer, gateway: ProviderGateway):
    annotations = ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True
    )

    @server.tool(annotations=annotations)
    async def get_provider_capabilities(
        provider_id: ProviderId | None = None,
        refresh: bool = False,
    ) -> Annotated[CallToolResult, CapabilitiesResponse]:
        """Inspect state; refresh discovers enabled providers without calling scholarly tools."""
        try:
            return result(GatewaySuccess(data=await gateway.capabilities(provider_id, refresh)))
        except GatewayError as exc:
            return result(GatewayFailure(error=exc.issue))

    @server.tool(annotations=annotations)
    async def search_scholarly_sources(
        request: SearchRequest,
    ) -> Annotated[CallToolResult, SearchResponse]:
        """Search Saadi Tafsir sources; passage scoping requires explicit verified mapping."""
        try:
            return result(GatewaySuccess(data=await gateway.search(request)))
        except GatewayError as exc:
            return result(GatewayFailure(error=exc.issue, issues=getattr(exc, "issues", ())))
