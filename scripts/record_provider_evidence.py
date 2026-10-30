"""Opt-in LIVE provider evidence recorder. Contacts the real hosted providers.

Usage: record_provider_evidence.py --source-root /abs/wirdi-Ai --out PATH.json

Records discovery, signature admission, search outcomes and response digests only.
Provider excerpts are never written; results are never mocked.
"""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from wirdi_mcp.domain.models import PassageSelection
from wirdi_mcp.providers.config import GatewaySettings, ProviderSettings
from wirdi_mcp.providers.gateway import ProviderGateway
from wirdi_mcp.providers.models import GatewayError, SearchRequest, SourceIdentity
from wirdi_mcp.quran.source import PublicSourceRepository

PROVIDERS = ("quran_mcp", "tafsir_mcp", "quran_search_mcp")
SEARCHABLE = ("quran_mcp", "tafsir_mcp")


def summarize(result):
    return {
        "hits": len(result.hits),
        "partial": result.partial,
        "mapping_status": result.mapping_status,
        "attempts": [a.model_dump() for a in result.attempts],
        "issues": [i.model_dump() for i in result.issues],
        "warnings": list(result.warnings),
        "hit_records": [
            {
                "provider_tool": h.provider_tool,
                "compatibility": h.compatibility,
                "validation_status": h.validation_status,
                "source_reference": h.source_reference.model_dump(),
                "citation_work_id": h.citation.work_id,
                "citation_title": h.citation.title,
                "response_sha256": h.response_sha256,
                "excerpt_sha256": h.excerpt_sha256,
                "mapping_sha256": h.mapping_sha256,
            }
            for h in result.hits
        ],
    }


async def attempt(label, call):
    started = datetime.now(UTC).isoformat()
    try:
        return {"check": label, "started": started, "outcome": "contacted", **summarize(await call)}
    except GatewayError as exc:
        issues = [i.model_dump() for i in getattr(exc, "issues", ())] or [exc.issue.model_dump()]
        return {"check": label, "started": started, "outcome": "error", "issues": issues}


async def main(root: Path, out: Path):
    repo = PublicSourceRepository(root)
    settings = GatewaySettings(
        providers=tuple(ProviderSettings(provider_id=p, enabled=True) for p in PROVIDERS)
    )
    gateway = ProviderGateway(repo, settings=settings)
    record = {"recorded_at": datetime.now(UTC).isoformat(), "discovery": [], "checks": []}
    caps = await gateway.capabilities(refresh=True)
    for state in caps.providers:
        profile = gateway.catalog[state.provider_id]
        discovered = {t.tool_name: t for t in state.tools}
        record["discovery"].append(
            {
                "provider_id": state.provider_id,
                "status": state.status,
                "issues": [i.model_dump() for i in state.issues],
                "discovered_tool_count": len(discovered),
                "admitted": sorted(t for t, c in discovered.items() if c.admitted),
                "catalog_expected": sorted(profile["admitted_tools"]),
                "catalog_signatures_match": all(
                    n in discovered and discovered[n].signature_sha256 == v["signature_sha256"]
                    for n, v in profile["admitted_tools"].items()
                ),
            }
        )
    hafs = repo.manifest["editions"]["hafs"]

    def identity(pid):
        return SourceIdentity(
            corpus_id=hafs["corpus_id"],
            corpus_version=hafs["version"],
            numbering_system=hafs["numbering_system"],
            provider_sources={pid: gateway.catalog[pid]["source_id"]},
        )

    def scoped(pid, surah, lo, hi):
        return SearchRequest(
            query="الصبر",
            limit=2,
            provider_ids=(pid,),
            selection=PassageSelection(start=repo.reference("qalun", surah, lo), end_ayah=hi),
            source_identity=identity(pid),
        )

    for pid in SEARCHABLE:
        request = SearchRequest(query="الصبر", limit=2, provider_ids=(pid,))
        record["checks"].append(await attempt(f"{pid}:broad", gateway.search(request)))
        record["checks"].append(
            await attempt(f"{pid}:scoped:qalun6:1-8", gateway.search(scoped(pid, 6, 1, 8)))
        )
        record["checks"].append(
            await attempt(
                f"{pid}:scoped:qalun2:27-27(review-required)",
                gateway.search(scoped(pid, 2, 27, 27)),
            )
        )
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for c in record["checks"]:
        codes = [i["code"] for i in c.get("issues", [])]
        print(c["check"], c["outcome"], "hits=" + str(c.get("hits")), codes)
    print(
        [
            (d["provider_id"], d["status"], d["catalog_signatures_match"])
            for d in record["discovery"]
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.source_root, args.out))
