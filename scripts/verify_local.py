"""Local stdio verification; reads only configured public files, never a database."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from wirdi_mcp.domain.models import PassageSelection
from wirdi_mcp.quran.source import PublicSourceRepository
from wirdi_mcp.tools.contracts import MappingToolResponse, PassageToolResponse


async def verify(source_root: Path | None) -> dict:
    repository = (
        PublicSourceRepository(source_root) if source_root else PublicSourceRepository.bundled()
    )
    selection = PassageSelection(start=repository.reference("qalun", 6, 1), end_ayah=8)
    target = repository.manifest["editions"]["hafs"]
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "wirdi_mcp.server"],
        env={
            **({"WIRDI_AI_ROOT": str(source_root)} if source_root else {}),
            "WIRDI_MCP_LOG_LEVEL": "ERROR",
        },
    )
    async with asyncio.timeout(30), Client(params, read_timeout_seconds=10) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools.tools} == {
            "health_check",
            "get_qaloun_passage",
            "resolve_source_mapping",
            "list_tajwid_rules",
            "get_tajwid_rule",
            "analyze_qaloun_tajwid",
            "summarize_tajwid",
            "analyze_app_page",
            "list_reading_combinations",
            "get_letter_properties",
            "get_source_page",
            "search_source_pages",
        }
        passage_result = await client.call_tool(
            "get_qaloun_passage",
            {"selection": selection.model_dump(mode="json")},
        )
        if passage_result.is_error:
            raise RuntimeError(
                "Passage call failed; inspect source configuration and pinned checksums"
            )
        passage = PassageToolResponse.model_validate(passage_result.structured_content).root
        assert passage.status == "ok" and len(passage.data.ayat) == 8
        mapping_result = await client.call_tool(
            "resolve_source_mapping",
            {
                "selection": selection.model_dump(mode="json"),
                "target_corpus_id": target["corpus_id"],
                "target_corpus_version": target["version"],
                "target_numbering_system": target["numbering_system"],
            },
        )
        if mapping_result.is_error:
            raise RuntimeError(
                "Mapping call failed; inspect source configuration and pinned checksums"
            )
        mapping = MappingToolResponse.model_validate(mapping_result.structured_content).root
        assert mapping.status == "ok" and mapping.data.mapping_status == "verified_difference"
        ranges = [(r.start.surah, r.start.ayah, r.end_ayah) for r in mapping.data.source_reference]
        assert ranges == [(6, 1, 7)] and mapping.data.safe_for_source_retrieval
        health = await client.call_tool("health_check", {})
        assert not health.is_error
        return {
            "tools": [t.name for t in tools.tools],
            "protocol": client.protocol_version,
            "service_version": health.structured_content["service_version"],
            "corpus_sha256": passage.data.snapshot_sha256,
            "ayat_returned": 8,
            "canonical_selection": "6:1-8",
            "source_selection": "6:1-7",
            "mapping_status": mapping.data.mapping_status,
            "validation_status": "machine_checked",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root", type=Path, help="optional Wirdi AI checkout; default: bundled"
    )
    args = parser.parse_args()
    print(
        json.dumps(
            asyncio.run(verify(args.source_root.resolve() if args.source_root else None)), indent=2
        )
    )
