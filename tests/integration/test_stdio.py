"""Real local MCP calls only; no external provider calls or corpus access."""

import asyncio
import sys

from conftest import selection
from mcp import Client, StdioServerParameters

from wirdi_mcp.quran.source import PublicSourceRepository


def test_stdio_handshake_discovery_call_and_unavailable_tool(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "wirdi_mcp.server"],
            cwd=tmp_path,
            env={"WIRDI_MCP_LOG_LEVEL": "ERROR"},
        )
        async with asyncio.timeout(20), Client(params, read_timeout_seconds=5) as client:
            assert client.protocol_version
            assert client.server_info.name == "wirdi-mcp"
            listed = await client.list_tools()
            assert {tool.name for tool in listed.tools} == {
                "health_check",
                "get_qaloun_passage",
                "resolve_source_mapping",
                "get_provider_capabilities",
                "search_scholarly_sources",
            }
            tool = listed.tools[0]
            assert tool.annotations.read_only_hint is True
            assert tool.output_schema
            result = await client.call_tool("health_check", {})
            assert not result.is_error
            payload = result.structured_content
            assert payload["status"] == "foundation_ready"
            assert payload["external_providers"] == "disabled"
            assert payload["tajwid_analysis"] == "not_implemented"
            assert payload["validation_status"] == "not_applicable"
            assert payload["quran_data"] == "not_configured"
            result = await client.call_tool(
                "get_qaloun_passage",
                {
                    "selection": selection(PublicSourceRepository(None)).model_dump(mode="json"),
                },
            )
            assert result.is_error
            assert result.structured_content["error"]["code"] == "DATA_UNAVAILABLE"
            unsupported = await client.call_tool("analyze_qaloun_tajwid", {})
            assert unsupported.is_error

    asyncio.run(run())
