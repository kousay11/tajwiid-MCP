"""Every request of docs/APPLY.json is run against the real server, so the examples cannot drift."""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[2]
APPLY = json.loads((ROOT / "docs" / "APPLY.json").read_text("utf-8"))
REQUESTS = APPLY["requests"]


def _missing(needs):
    for need in needs:
        if need == "WIRDI_AI_ROOT" and not os.environ.get("WIRDI_TEST_SOURCE_ROOT"):
            return "Set WIRDI_TEST_SOURCE_ROOT for read-only real-source checks"
        if need.startswith("local_page_store:"):
            edition = need.split(":", 1)[1]
            if not (ROOT / "knowledge" / "sources" / edition / "pages.jsonl").is_file():
                return f"no local page store for {edition} on this machine"
    return None


def test_the_file_lists_every_tool_and_every_id_is_unique():
    tools = {r["tool"] for r in REQUESTS}
    assert tools == {
        "health_check",
        "get_qaloun_passage",
        "resolve_source_mapping",
        "list_tajwid_rules",
        "get_tajwid_rule",
        "analyze_qaloun_tajwid",
        "summarize_tajwid",
        "analyze_app_page",
        "get_letter_properties",
        "get_source_page",
        "search_source_pages",
        "get_tajwid_explanation",
    }
    ids = [r["id"] for r in REQUESTS]
    assert len(ids) == len(set(ids))
    assert all(
        {"id", "tool", "purpose", "arguments", "expect", "needs"} <= set(r) for r in REQUESTS
    )


@pytest.mark.parametrize("request_", REQUESTS, ids=[r["id"] for r in REQUESTS])
def test_each_example_behaves_as_documented(request_, tmp_path):
    reason = _missing(request_["needs"])
    if reason:
        pytest.skip(reason)
    env = {"WIRDI_MCP_LOG_LEVEL": "ERROR"}
    if os.environ.get("WIRDI_TEST_SOURCE_ROOT"):
        env["WIRDI_AI_ROOT"] = os.environ["WIRDI_TEST_SOURCE_ROOT"]
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "wirdi_mcp.server"], cwd=tmp_path, env=env
    )

    async def run():
        async with asyncio.timeout(60), Client(params, read_timeout_seconds=30) as client:
            return await client.call_tool(request_["tool"], request_["arguments"])

    result = asyncio.run(run())
    payload = result.structured_content
    expect = request_["expect"]
    assert payload["status"] == expect["status"], (request_["id"], payload.get("error"))
    if "code" in expect:
        assert payload["error"]["code"] == expect["code"], request_["id"]
