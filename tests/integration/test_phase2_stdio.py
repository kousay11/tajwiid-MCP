"""Real local MCP calls against opt-in public files."""

import asyncio
import sys

from conftest import selection, target
from jsonschema import validate
from mcp import Client, StdioServerParameters


def test_real_stdio_quran_tools_errors_and_read_only_metadata(real_repo, tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "wirdi_mcp.server"],
            cwd=tmp_path,
            env={"WIRDI_MCP_LOG_LEVEL": "ERROR", "WIRDI_AI_ROOT": str(real_repo.root)},
        )
        async with asyncio.timeout(30), Client(params, read_timeout_seconds=10) as client:
            tools = (await client.list_tools()).tools
            assert {t.name for t in tools} == {
                "health_check",
                "get_qaloun_passage",
                "resolve_source_mapping",
                "get_tajwid_rule",
                "list_tajwid_rules",
                "analyze_qaloun_tajwid",
                "summarize_tajwid",
                "analyze_app_page",
                "get_tajwid_explanation",
                "get_source_page",
                "search_source_pages",
                "get_letter_properties",
            }
            schemas = {t.name: t.output_schema for t in tools}
            for tool in tools:
                assert tool.annotations.read_only_hint is True
                assert tool.annotations.destructive_hint is False
                assert tool.output_schema
            args = {"selection": selection(real_repo).model_dump(mode="json")}
            result = await client.call_tool("get_qaloun_passage", args)
            assert not result.is_error
            validate(result.structured_content, schemas["get_qaloun_passage"])
            payload = result.structured_content
            assert payload["status"] == "ok" and len(payload["data"]["ayat"]) == 8
            result = await client.call_tool("resolve_source_mapping", {**args, **target(real_repo)})
            assert not result.is_error
            validate(result.structured_content, schemas["resolve_source_mapping"])
            data = result.structured_content["data"]
            assert data["mapping_status"] == "verified_difference"
            assert data["source_reference"][0]["end_ayah"] == 7
            assert data["safe_for_source_retrieval"]
            review_args = {"selection": selection(real_repo, 2, 27, 27).model_dump(mode="json")}
            result = await client.call_tool(
                "resolve_source_mapping", {**review_args, **target(real_repo)}
            )
            assert not result.is_error
            assert result.structured_content["data"]["mapping_status"] == "mapping_requires_review"
            assert not result.structured_content["data"]["safe_for_source_retrieval"]
            invalid = {"selection": selection(real_repo, 2, 286, 286).model_dump(mode="json")}
            result = await client.call_tool("get_qaloun_passage", invalid)
            assert result.is_error
            validate(result.structured_content, schemas["get_qaloun_passage"])
            assert result.structured_content["error"]["code"] == "INVALID_REFERENCE"
            invalid = {"selection": selection(real_repo).model_dump(mode="json")}
            invalid["selection"]["start"]["corpus_version"] = "unknown"
            result = await client.call_tool("get_qaloun_passage", invalid)
            assert (
                result.is_error
                and result.structured_content["error"]["code"] == "UNSUPPORTED_VERSION"
            )
            result = await client.call_tool("health_check", {})
            assert result.structured_content["quran_data"] == "configured_unchecked"
            tajwid = await client.call_tool(
                "analyze_qaloun_tajwid",
                {
                    "selection": args["selection"],
                    "reading_context": {"mode": "wasl"},
                },
            )
            assert not tajwid.is_error
            data = tajwid.structured_content["data"]
            assert data["annotations"] and data["total"] >= len(data["annotations"])
            for annotation in data["annotations"]:
                assert annotation["status"] == "candidate"
                assert annotation["evidence"] and annotation["page_refs"]["app_page_start"]
                assert annotation["reading_context"]["mode"] == "wasl"
            explanation = await client.call_tool(
                "get_tajwid_explanation",
                {"annotation_id": "x", "annotation_version": "1"},
            )
            assert explanation.structured_content["error"]["code"] == "UNSUPPORTED_CAPABILITY"

    asyncio.run(run())
