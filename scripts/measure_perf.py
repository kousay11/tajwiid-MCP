#!/usr/bin/env python3
"""Measure cold start and per-call latency of the real stdio server (read-only).

Usage: measure_perf.py [--source-root /path/to/wirdi-Ai] [--runs 30]
"""

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path

from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
QALOUN = {
    "corpus_id": "wirdi-ai:quranpedia:qalun",
    "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
    "numbering_system": "wirdi-ai:qalun-6214",
    "riwaya": "qaloun",
    "tariq": "unspecified",
}


def selection(surah, first, last):
    return {"start": {**QALOUN, "surah": surah, "ayah": first}, "end_ayah": last}


def percentile(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


async def measure(source_root: str | None, runs: int) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "wirdi_mcp.server"],
        cwd=ROOT,
        env={
            "WIRDI_MCP_LOG_LEVEL": "ERROR",
            **({"WIRDI_AI_ROOT": source_root} if source_root else {}),
        },
    )
    started = time.perf_counter()
    async with Client(params, read_timeout_seconds=30) as client:
        await client.list_tools()
        print(f"cold start to first tools/list: {time.perf_counter() - started:.2f} s")
        ctx = {"mode": "waqf"}
        cases = {
            "1 ayah (analyze)": (
                "analyze_qaloun_tajwid",
                {"selection": selection(18, 45, 45), "reading_context": ctx},
            ),
            "8 ayat (analyze)": (
                "analyze_qaloun_tajwid",
                {"selection": selection(18, 45, 52), "reading_context": ctx},
            ),
            "50 ayat (analyze, 100 rows)": (
                "analyze_qaloun_tajwid",
                {"selection": selection(2, 1, 50), "reading_context": ctx},
            ),
            "100 ayat (analyze, largest page: 500 rows)": (
                "analyze_qaloun_tajwid",
                {"selection": selection(2, 1, 100), "reading_context": ctx, "limit": 500},
            ),
            "1 surah (summarize, Kahf)": (
                "summarize_tajwid",
                {"surah": 18, "reading_context": ctx},
            ),
            "longest surah (summarize, Baqara)": (
                "summarize_tajwid",
                {"surah": 2, "reading_context": ctx},
            ),
            "1 app page (analyze_app_page)": (
                "analyze_app_page",
                {"page": 263, "reading_context": ctx},
            ),
            "get_tajwid_rule": ("get_tajwid_rule", {"rule_id": "qalqala_kubra", "version": "1"}),
        }
        print("| call | p50 ms | p95 ms | max ms |\n| --- | ---: | ---: | ---: |")
        for label, (tool, args) in cases.items():
            times = []
            for _ in range(runs):
                t0 = time.perf_counter()
                result = await client.call_tool(tool, args)
                times.append((time.perf_counter() - t0) * 1000)
                assert not result.is_error, (label, result.structured_content)
            print(
                f"| {label} | {statistics.median(times):.0f} | {percentile(times, 0.95):.0f} "
                f"| {max(times):.0f} |"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", help="optional Wirdi AI checkout; default: bundled")
    parser.add_argument("--runs", type=int, default=30)
    args = parser.parse_args()
    asyncio.run(measure(args.source_root, args.runs))
