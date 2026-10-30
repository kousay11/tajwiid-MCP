"""Protocol tests use deterministic peers and no external network access."""

import asyncio

from jsonschema import validate
from mcp import Client

from wirdi_mcp.config import Settings
from wirdi_mcp.server import create_server


def test_default_provider_tools_publish_schemas_and_explicit_unavailability():
    async def run():
        async with Client(create_server(Settings())) as client:
            tools = {t.name: t for t in (await client.list_tools()).tools}
            assert len(tools) == 5
            result = await client.call_tool("get_provider_capabilities", {})
            assert not result.is_error
            validate(result.structured_content, tools["get_provider_capabilities"].output_schema)
            assert all(
                p["status"] == "disabled" for p in result.structured_content["data"]["providers"]
            )
            result = await client.call_tool(
                "search_scholarly_sources", {"request": {"query": "public"}}
            )
            assert result.is_error
            validate(result.structured_content, tools["search_scholarly_sources"].output_schema)
            assert result.structured_content["error"]["code"] == "PROVIDER_UNAVAILABLE"

    asyncio.run(run())


def test_bad_provider_configuration_does_not_disable_existing_tools(tmp_path):
    async def run():
        async with Client(
            create_server(Settings(provider_config=tmp_path / "missing.json"))
        ) as client:
            cap = await client.call_tool("get_provider_capabilities", {"refresh": True})
            assert cap.is_error and cap.structured_content["error"]["code"] == "INVALID_CONFIG"
            health = await client.call_tool("health_check", {})
            assert not health.is_error and health.structured_content["status"] == "foundation_ready"
            assert health.structured_content["external_providers"] == "configured_unchecked"

    asyncio.run(run())


def test_original_mapping_review_rejected_before_external_discovery(real_repo):
    import pytest
    from conftest import selection, target

    from wirdi_mcp.providers.config import GatewaySettings, ProviderSettings
    from wirdi_mcp.providers.gateway import ProviderGateway
    from wirdi_mcp.providers.models import GatewayError, SearchRequest

    async def run():
        def forbidden(*args):
            raise AssertionError("External discovery must not happen for an unsafe mapping")

        g = ProviderGateway(
            real_repo,
            connector=forbidden,
            settings=GatewaySettings(
                providers=(ProviderSettings(provider_id="quran_mcp", enabled=True),),
            ),
        )
        identity = target(real_repo)
        with pytest.raises(GatewayError) as error:
            await g.search(
                SearchRequest(
                    query="public",
                    selection=selection(real_repo, 2, 27, 27),
                    source_identity={
                        "corpus_id": identity["target_corpus_id"],
                        "corpus_version": identity["target_corpus_version"],
                        "numbering_system": identity["target_numbering_system"],
                        "provider_sources": {"quran_mcp": g.catalog["quran_mcp"]["source_id"]},
                    },
                )
            )
        assert error.value.issue.code == "AMBIGUOUS_MAPPING"

    asyncio.run(run())
