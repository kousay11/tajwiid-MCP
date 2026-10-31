"""Real local MCP calls only; no network access or corpus access."""

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
                "get_tajwid_rule",
                "analyze_qaloun_tajwid",
                "get_tajwid_explanation",
            }
            tool = listed.tools[0]
            assert tool.annotations.read_only_hint is True
            assert tool.output_schema
            result = await client.call_tool("health_check", {})
            assert not result.is_error
            payload = result.structured_content
            assert payload["status"] == "foundation_ready"
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


def test_tool_list_is_valid_for_legacy_protocol_versions():
    """2025 protocol versions require a top-level object type on every output schema."""
    import json
    import subprocess

    def rpc(proc, message):
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()

    for version in ("2025-06-18", "2025-11-25"):
        proc = subprocess.Popen(
            [sys.executable, "-m", "wirdi_mcp.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env={"WIRDI_MCP_LOG_LEVEL": "ERROR"},
        )
        try:
            rpc(
                proc,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": version,
                        "capabilities": {},
                        "clientInfo": {"name": "legacy", "version": "1"},
                    },
                },
            )
            proc.stdout.readline()
            rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
            rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            reply = json.loads(proc.stdout.readline())
        finally:
            proc.kill()
        assert "error" not in reply, reply
        assert len(reply["result"]["tools"]) == 6
        assert all(t["outputSchema"]["type"] == "object" for t in reply["result"]["tools"])
