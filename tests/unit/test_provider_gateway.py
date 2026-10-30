"""Deterministic fake MCP peers. These are never reported as live integrations."""

import asyncio
import copy
import json
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool, ToolAnnotations
from pydantic import ValidationError

from wirdi_mcp.providers.config import GatewaySettings, ProviderSettings, load_settings
from wirdi_mcp.providers.gateway import ProviderGateway
from wirdi_mcp.providers.models import GatewayError, SearchRequest, signature_schema
from wirdi_mcp.providers.transport import MAX_BYTES, decode, schema_signature
from wirdi_mcp.quran.source import PublicSourceRepository


def response(data):
    return CallToolResult(
        structured_content=data, content=[TextContent(type="text", text=json.dumps(data))]
    )


def fixtures():
    return {
        "fetch_grounding_rules": response({"text": "Untrusted guidance; never executable"}),
        "search_tafsir": response(
            {
                "results": [
                    {
                        "ayah_key": "6:1",
                        "surah": 6,
                        "ayah": 1,
                        "tafsir_text": "  SENTINEL e\u0301  ",
                        "citation": {
                            "edition_id": "ar-saadi",
                            "edition_name": "Fixture work",
                            "author": "Fixture author",
                        },
                    }
                ],
                "pagination": {"has_more": False},
            }
        ),
        "fetch_quran": response(
            {
                "results": {"ar-uthmani-hafs": [{"ayah": "6:1", "text": "SENTINEL"}]},
                "pagination": {"has_more": False},
            }
        ),
        "list_tafsir_sources": response(
            {
                "items": [
                    {"slug": "saadi", "name": "Fixture work", "attribution": "Fixture attribution"}
                ]
            }
        ),
        "search_in_tafsir": response(
            {
                "result": [
                    {
                        "surah": 6,
                        "ayah": 1,
                        "tafsir_excerpt": "SENTINEL",
                        "source_attribution": "Fixture attribution",
                    }
                ]
            }
        ),
        "fetch_ayah": response({"surah": 6, "ayah": 1, "text": "SENTINEL"}),
    }


class Peer:
    def __init__(self, tools, payloads):
        self.tools, self.payloads = tools, payloads
        self.calls = []
        self.pages = 0

    async def list_tools(self, cursor=None):
        self.pages += 1
        return ListToolsResult(tools=self.tools)

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        value = self.payloads[name]
        if isinstance(value, Exception):
            raise value
        if callable(value):
            return await value(name, args)
        return copy.deepcopy(value)


def gateway(*ids, policy=None):
    settings = policy or GatewaySettings(
        providers=tuple(ProviderSettings(provider_id=p, enabled=True) for p in ids),
        retries=0,
    )
    peers, connections, closed = {}, [], []

    @asynccontextmanager
    async def connector(provider, policy, profile):
        connections.append(provider.provider_id)
        try:
            yield peers[provider.provider_id]
        finally:
            closed.append(provider.provider_id)

    g = ProviderGateway(PublicSourceRepository(None), settings=settings, connector=connector)
    for pid in ids:
        profile = g.catalog[pid]
        profile["min_interval_seconds"] = 0
        tools = []
        for name, admitted in profile["admitted_tools"].items():
            tool = Tool(
                name=name,
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                annotations=ToolAnnotations(read_only_hint=True),
            )
            admitted["signature_sha256"] = schema_signature(tool)
            tools.append(tool)
        tools.append(
            Tool(
                name="settings_update",
                input_schema={"type": "object"},
                annotations=ToolAnnotations(read_only_hint=False),
            )
        )
        peers[pid] = Peer(tools, fixtures())
    return g, peers, connections, closed


def run(coro):
    return asyncio.run(coro)


def test_discovery_preserves_schemas_and_denies_mutating_tools():
    g, peers, opened, closed = gateway("quran_mcp")

    async def check():
        cached = await g.capabilities()
        assert opened == [] and cached.providers[0].status == "not_discovered"
        result = await g.capabilities(refresh=True)
        state = result.providers[0]
        assert state.status == "ready"
        denied = next(t for t in state.tools if t.tool_name == "settings_update")
        assert not denied.admitted
        assert denied.input_schema == {"type": "object"}
        assert peers["quran_mcp"].calls == []

    run(check())
    assert opened == closed == ["quran_mcp"]


def test_broad_response_keeps_exact_text_attribution_and_unknown_edition():
    g, peers, _, _ = gateway("quran_mcp")
    result = run(g.search(SearchRequest(query="public", provider_ids=("quran_mcp",))))
    hit = result.hits[0]
    assert hit.excerpt == "  SENTINEL e\u0301  " and hit.citation.author == "Fixture author"
    assert hit.compatibility == "unknown" and hit.citation.publication is None
    assert hit.source_reference.dataset_version is None
    assert hit.validation_status == "unreviewed"
    assert [name for name, _ in peers["quran_mcp"].calls] == [
        "fetch_grounding_rules",
        "search_tafsir",
    ]


def test_fallback_preserves_failure_and_uses_only_compatible_search_adapter():
    g, peers, _, _ = gateway("quran_mcp", "tafsir_mcp", "quran_search_mcp")
    peers["quran_mcp"].payloads["search_tafsir"] = OSError("SENSITIVE SENTINEL")
    result = run(g.search(SearchRequest(query="public")))
    assert result.hits[0].provider_id == "tafsir_mcp" and result.partial
    assert [a.outcome for a in result.attempts] == ["failed", "success"]
    assert "SENSITIVE" not in result.model_dump_json()
    assert peers["quran_search_mcp"].calls == []


@pytest.mark.parametrize(
    "bad",
    [
        {"results": "invalid"},
        {"results": [{"surah": 6, "ayah": 1, "ayah_key": "6:1", "tafsir_text": "SENTINEL"}]},
        {
            "results": [
                {
                    "surah": 6,
                    "ayah": 1,
                    "ayah_key": "6:1-3",
                    "ayah_keys": ["6:1", "6:3"],
                    "tafsir_text": "SENTINEL",
                    "citation": {
                        "edition_id": "ar-saadi",
                        "edition_name": "Fixture",
                        "author": "Fixture",
                    },
                }
            ]
        },
    ],
)
def test_malformed_or_unattributed_payload_never_becomes_evidence(bad):
    g, peers, _, _ = gateway("quran_mcp")
    peers["quran_mcp"].payloads["search_tafsir"] = response(bad)
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public")))
    assert error.value.issues[0].code in {"SCHEMA_MISMATCH", "UNVERIFIED_EVIDENCE"}


def test_schema_drift_is_rejected_without_invoking_the_changed_tool():
    g, peers, _, _ = gateway("quran_mcp")
    tool = next(t for t in peers["quran_mcp"].tools if t.name == "search_tafsir")
    tool.input_schema["required"] = ["new_argument"]
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public")))
    assert error.value.issues[0].code == "SCHEMA_MISMATCH"
    assert all(name != "search_tafsir" for name, _ in peers["quran_mcp"].calls)


def test_retry_is_bounded_and_session_is_closed():
    settings = GatewaySettings(
        providers=(ProviderSettings(provider_id="quran_mcp", enabled=True),), retries=1
    )
    g, peers, opened, closed = gateway("quran_mcp", policy=settings)

    async def transient(name, args):
        if len(opened) == 1:
            raise OSError("temporary")
        return fixtures()["search_tafsir"]

    peers["quran_mcp"].payloads["search_tafsir"] = transient
    assert run(g.search(SearchRequest(query="public"))).hits
    assert len(opened) == 2 and opened == closed


def test_timeout_and_cancellation_close_sessions():
    settings = GatewaySettings(
        providers=(ProviderSettings(provider_id="quran_mcp", enabled=True),),
        operation_timeout_seconds=0.1,
        total_timeout_seconds=1,
        retries=0,
    )
    g, peers, opened, closed = gateway("quran_mcp", policy=settings)

    async def slow(name, args):
        await asyncio.sleep(5)

    peers["quran_mcp"].payloads["search_tafsir"] = slow
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public")))
    assert error.value.issues[0].code == "PROVIDER_TIMEOUT" and opened == closed

    async def cancel():
        task = asyncio.create_task(g.search(SearchRequest(query="public")))
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    run(cancel())


def test_unsafe_mapping_rejected_before_network(monkeypatch):
    from wirdi_mcp.mapping.adapter import WirdiSourceMappingAdapter

    g, _, opened, _ = gateway("quran_mcp")

    async def review(*args):
        return SimpleNamespace(safe_for_source_retrieval=False)

    monkeypatch.setattr(WirdiSourceMappingAdapter, "resolve", review)
    from conftest import selection

    request = SearchRequest(
        query="public",
        selection=selection(g.repository),
        source_identity={
            "corpus_id": "explicit",
            "corpus_version": "explicit",
            "numbering_system": "explicit",
            "provider_sources": {"quran_mcp": g.catalog["quran_mcp"]["source_id"]},
        },
    )
    with pytest.raises(GatewayError) as error:
        run(g.search(request))
    assert error.value.issue.code == "AMBIGUOUS_MAPPING" and not opened


def scoped(g):
    from conftest import selection

    return SearchRequest(
        query="public",
        selection=selection(g.repository),
        source_identity={
            "corpus_id": "explicit",
            "corpus_version": "explicit",
            "numbering_system": "explicit",
            "provider_sources": {"quran_mcp": g.catalog["quran_mcp"]["source_id"]},
        },
    )


@pytest.mark.parametrize("matches", [True, False])
def test_provider_boundary_guard_and_explicit_mapped_coordinates(matches):
    g, peers, _, _ = gateway("quran_mcp")

    async def scope(request):
        return (
            SimpleNamespace(mapping_artifact_sha256="a" * 64, mapping_status="verified_difference"),
            {(6, 1): "SENTINEL"},
            lambda s: s,
        )

    g.prepare_scope = scope
    if not matches:
        peers["quran_mcp"].payloads["fetch_quran"] = response(
            {"results": {"ar-uthmani-hafs": [{"ayah": "6:1", "text": "OTHER"}]}}
        )
        with pytest.raises(GatewayError) as error:
            run(g.search(scoped(g)))
        assert error.value.issues[0].code == "INCOMPATIBLE_RIWAYA"
        assert not any(n == "search_tafsir" for n, _ in peers["quran_mcp"].calls)
    else:
        result = run(g.search(scoped(g)))
        assert result.hits[0].compatibility == "mapped_boundaries_checked"
        args = next(a for n, a in peers["quran_mcp"].calls if n == "search_tafsir")
        assert args["ayahs"] == ["6:1"]  # Never the canonical Qaloun 6:1-8 selection.


def test_disabled_defaults_and_invalid_config_do_not_connect(tmp_path):
    g = ProviderGateway(PublicSourceRepository(None))
    result = run(g.capabilities(refresh=True))
    assert all(p.status == "disabled" for p in result.providers)
    with pytest.raises(GatewayError):
        run(g.search(SearchRequest(query="public")))
    p = tmp_path / "providers.json"
    p.write_text('{"providers":[{"provider_id":"unknown","enabled":true}]}')
    with pytest.raises(GatewayError) as error:
        load_settings(p)
    assert error.value.issue.code == "INVALID_CONFIG"
    with pytest.raises(ValidationError):
        SearchRequest(query="public", source_identity={})


def test_decoder_size_malformed_json_and_no_remote_schema_refs():
    from wirdi_mcp.providers.transport import validate

    with pytest.raises(GatewayError):
        decode(
            CallToolResult(content=[TextContent(type="text", text='{"duplicate":1,"duplicate":2}')])
        )
    with pytest.raises(GatewayError):
        decode(response({"text": "x" * MAX_BYTES}))
    with pytest.raises(GatewayError):
        validate({}, {"$ref": "https://untrusted.invalid/schema"})
    assert signature_schema({"properties": {"title": {"type": "integer"}}})["properties"][
        "title"
    ] == {"type": "integer"}


def test_repeated_discovery_cursor_rejected():
    g, peers, _, _ = gateway("quran_mcp")

    async def pages(cursor=None):
        return ListToolsResult(tools=[], next_cursor="cycle")

    peers["quran_mcp"].list_tools = pages
    state = run(g.capabilities(refresh=True)).providers[0]
    assert state.status == "unavailable" and state.issues[0].code == "SCHEMA_MISMATCH"


def test_config_rejects_relative_oversized_duplicate_and_malformed_values(tmp_path):
    for path in (Path("providers.json"), tmp_path / "missing.json"):
        with pytest.raises(GatewayError) as error:
            load_settings(path)
        assert error.value.issue.code == "INVALID_CONFIG"
    big = tmp_path / "big.json"
    big.write_text(" " * 70000 + '{"providers":[]}')
    with pytest.raises(GatewayError):
        load_settings(big)
    ok = tmp_path / "ok.json"
    ok.write_text('{"providers":[{"provider_id":"quran_mcp","enabled":true}]}')
    assert load_settings(ok).providers[0].enabled
    with pytest.raises(ValidationError):
        GatewaySettings(
            providers=(
                ProviderSettings(provider_id="quran_mcp"),
                ProviderSettings(provider_id="quran_mcp"),
            )
        )
    with pytest.raises(ValidationError):
        ProviderSettings(provider_id="quran_mcp", bearer_token_env="lower-case")


@pytest.mark.parametrize(
    "bad",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "x", "limit": 0},
        {"query": "x", "limit": 21},
        {"query": "x", "provider_ids": ("quran_mcp", "quran_mcp")},
        {"query": "x", "provider_ids": ("unknown",)},
        {"query": "x", "work_id": "ibn_kathir"},
    ],
)
def test_search_request_rejects_invalid_input(bad):
    with pytest.raises(ValidationError):
        SearchRequest(**bad)


def test_discovery_only_provider_is_never_called_for_search():
    g, peers, opened, _ = gateway("quran_mcp", "quran_search_mcp")
    assert g.catalog["quran_search_mcp"]["admitted_tools"] == {}
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public", provider_ids=("quran_search_mcp",))))
    assert error.value.issues[0].code == "UNSUPPORTED_CAPABILITY"
    assert opened == [] and peers["quran_search_mcp"].calls == []


def test_disabled_provider_is_not_contacted_when_explicitly_requested():
    g, _, opened, _ = gateway("quran_mcp")
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public", provider_ids=("tafsir_mcp",))))
    assert error.value.issues[0].code == "PROVIDER_UNAVAILABLE" and opened == []


def test_mutating_flagged_or_absent_admitted_tool_is_never_invoked():
    g, peers, _, _ = gateway("quran_mcp")
    next(
        t for t in peers["quran_mcp"].tools if t.name == "search_tafsir"
    ).annotations = ToolAnnotations(read_only_hint=False)
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public")))
    assert error.value.issues[0].code == "SCHEMA_MISMATCH"
    assert all(n != "search_tafsir" for n, _ in peers["quran_mcp"].calls)
    g, peers, _, _ = gateway("quran_mcp")
    peers["quran_mcp"].tools[:] = [t for t in peers["quran_mcp"].tools if t.name != "search_tafsir"]
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public")))
    assert error.value.issues[0].code == "SCHEMA_MISMATCH"
    state = run(g.capabilities("quran_mcp", refresh=True)).providers[0]
    assert {t.tool_name for t in state.tools if t.admitted} == {
        "fetch_grounding_rules",
        "fetch_quran",
    }


def test_rate_limit_is_retried_once_then_succeeds():
    settings = GatewaySettings(
        providers=(ProviderSettings(provider_id="quran_mcp", enabled=True),), retries=1
    )
    g, peers, opened, closed = gateway("quran_mcp", policy=settings)

    async def limited(name, args):
        if len(opened) == 1:
            return CallToolResult(
                is_error=True, content=[TextContent(type="text", text="[rate_limited]")]
            )
        return fixtures()["search_tafsir"]

    peers["quran_mcp"].payloads["search_tafsir"] = limited
    assert run(g.search(SearchRequest(query="public"))).hits
    assert len(opened) == 2 and opened == closed


def test_authentication_failure_is_not_retried():
    settings = GatewaySettings(
        providers=(ProviderSettings(provider_id="quran_mcp", enabled=True),), retries=1
    )
    g, _, opened, closed = gateway("quran_mcp", policy=settings)

    @asynccontextmanager
    async def denied(provider, policy, profile):
        opened.append(provider.provider_id)
        raise GatewayError("AUTHENTICATION_FAILED", "denied")
        yield

    g.connector = denied
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public")))
    assert error.value.issues[0].code == "AUTHENTICATION_FAILED" and len(opened) == 1


def scoped_tafsir(g, source=None):
    from conftest import selection

    return SearchRequest(
        query="public",
        selection=selection(g.repository),
        source_identity={
            "corpus_id": "explicit",
            "corpus_version": "explicit",
            "numbering_system": "explicit",
            "provider_sources": {"tafsir_mcp": source or g.catalog["tafsir_mcp"]["source_id"]},
        },
    )


def fixed_scope(g):
    async def scope(request):
        return (
            SimpleNamespace(mapping_artifact_sha256="b" * 64, mapping_status="verified_difference"),
            {(6, 1): "SENTINEL"},
            lambda s: s,
        )

    g.prepare_scope = scope


def test_tafsir_provider_scoped_search_checks_boundaries_first():
    g, peers, _, _ = gateway("tafsir_mcp")
    fixed_scope(g)
    result = run(g.search(scoped_tafsir(g)))
    hit = result.hits[0]
    assert hit.compatibility == "mapped_boundaries_checked" and hit.provider_id == "tafsir_mcp"
    assert hit.citation.attribution == "Fixture attribution" and hit.citation.author is None
    names = [n for n, _ in peers["tafsir_mcp"].calls]
    assert names.index("fetch_ayah") < names.index("search_in_tafsir")
    args = next(a for n, a in peers["tafsir_mcp"].calls if n == "search_in_tafsir")
    assert args["surah"] == 6 and args["source"] == "saadi"


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"surah": 6, "ayah": 1, "text": "OTHER"}, "INCOMPATIBLE_RIWAYA"),
        ({"surah": 6, "ayah": 2, "text": "SENTINEL"}, "SCHEMA_MISMATCH"),
        ({"surah": "6", "ayah": 1, "text": "SENTINEL"}, "SCHEMA_MISMATCH"),
    ],
)
def test_tafsir_provider_boundary_failures_block_search(payload, code):
    g, peers, _, _ = gateway("tafsir_mcp")
    fixed_scope(g)
    peers["tafsir_mcp"].payloads["fetch_ayah"] = response(payload)
    with pytest.raises(GatewayError) as error:
        run(g.search(scoped_tafsir(g)))
    assert error.value.issues[0].code == code
    assert all(n != "search_in_tafsir" for n, _ in peers["tafsir_mcp"].calls)


def test_tafsir_attribution_mismatch_never_becomes_evidence():
    g, peers, _, _ = gateway("tafsir_mcp")
    peers["tafsir_mcp"].payloads["search_in_tafsir"] = response(
        {"result": [{"surah": 6, "ayah": 1, "tafsir_excerpt": "X", "source_attribution": "Other"}]}
    )
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public")))
    assert error.value.issues[0].code == "UNVERIFIED_EVIDENCE"
    peers["tafsir_mcp"].payloads["list_tafsir_sources"] = response({"items": []})
    with pytest.raises(GatewayError) as error:
        run(g.search(SearchRequest(query="public")))
    assert error.value.issues[0].code == "UNVERIFIED_EVIDENCE"


def test_scoped_search_requires_matching_explicit_provider_source():
    g, peers, opened, _ = gateway("tafsir_mcp")
    fixed_scope(g)
    with pytest.raises(GatewayError) as error:
        run(g.search(scoped_tafsir(g, source="another:namespace")))
    assert error.value.issues[0].code == "UNSUPPORTED_VERSION"
    assert opened == [] and peers["tafsir_mcp"].calls == []


def test_empty_result_is_reported_as_empty_not_as_failure():
    g, peers, _, _ = gateway("quran_mcp")
    peers["quran_mcp"].payloads["search_tafsir"] = response(
        {"results": [], "pagination": {"has_more": False}}
    )
    result = run(g.search(SearchRequest(query="public")))
    assert result.hits == () and result.attempts[0].outcome == "empty" and not result.issues
