"""Explicit opt-in LIVE HTTP checks. Never substitute mocked results here."""

import asyncio
import os

import pytest

from wirdi_mcp.providers.config import GatewaySettings, ProviderSettings
from wirdi_mcp.providers.gateway import ProviderGateway
from wirdi_mcp.providers.models import GatewayError, SearchRequest
from wirdi_mcp.quran.source import PublicSourceRepository

pytestmark = pytest.mark.skipif(
    os.getenv("WIRDI_TEST_LIVE_PROVIDERS") != "1",
    reason="Live MCP calls require WIRDI_TEST_LIVE_PROVIDERS=1",
)


@pytest.mark.parametrize("pid", ["quran_mcp", "tafsir_mcp", "quran_search_mcp"])
def test_live_discovery(pid):
    async def run():
        g = ProviderGateway(
            PublicSourceRepository(None),
            settings=GatewaySettings(
                providers=(ProviderSettings(provider_id=pid, enabled=True),),
            ),
        )
        result = await g.capabilities(pid, refresh=True)
        state = result.providers[0]
        if state.status != "ready":
            pytest.skip("Live provider unavailable: " + ",".join(i.code for i in state.issues))
        assert state.tools and all(t.evidence_level == "runtime_discovered" for t in state.tools)

    asyncio.run(run())


@pytest.mark.parametrize("pid", ["quran_mcp", "tafsir_mcp"])
def test_live_attributed_broad_search(pid):
    async def run():
        g = ProviderGateway(
            PublicSourceRepository(None),
            settings=GatewaySettings(
                providers=(ProviderSettings(provider_id=pid, enabled=True),),
            ),
        )
        try:
            result = await g.search(SearchRequest(query="الصبر", provider_ids=(pid,), limit=2))
        except GatewayError as exc:
            if getattr(exc, "issues", ()) and all(
                i.code in {"PROVIDER_UNAVAILABLE", "PROVIDER_TIMEOUT", "RATE_LIMITED"}
                for i in exc.issues
            ):
                pytest.skip("Live provider unavailable: " + ",".join(i.code for i in exc.issues))
            raise
        assert result.hits and all(
            h.citation.title and h.source_reference.source_id for h in result.hits
        )
        assert all(
            h.compatibility == "unknown" and h.validation_status == "unreviewed"
            for h in result.hits
        )

    asyncio.run(run())
