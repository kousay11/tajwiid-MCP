"""Offline transport tests: byte limits, error classification and tool admission."""

import asyncio

import httpx2
import pytest
from mcp.types import CallToolResult, TextContent, Tool, ToolAnnotations

from wirdi_mcp.providers.config import GatewaySettings, ProviderSettings, catalog
from wirdi_mcp.providers.models import GatewayError
from wirdi_mcp.providers.transport import (
    MAX_BYTES,
    Channel,
    LimitedTransport,
    PayloadLimitError,
    classify,
    connect,
    decode,
)


def run(coro):
    return asyncio.run(coro)


def limited(handler):
    transport = LimitedTransport()
    transport.inner = httpx2.MockTransport(handler)
    return httpx2.AsyncClient(transport=transport, follow_redirects=False)


def test_compressed_response_is_rejected():
    def handler(request):
        return httpx2.Response(200, headers={"content-encoding": "gzip"}, content=b"x")

    async def check():
        async with limited(handler) as client:
            await client.get("https://provider.invalid/")

    with pytest.raises(GatewayError) as error:
        run(check())
    assert error.value.issue.code == "SCHEMA_MISMATCH"


def test_declared_oversize_body_is_rejected():
    def handler(request):
        return httpx2.Response(200, headers={"content-length": str(MAX_BYTES + 1)}, content=b"x")

    async def check():
        async with limited(handler) as client:
            await client.get("https://provider.invalid/")

    with pytest.raises(PayloadLimitError):
        run(check())


def test_undeclared_oversize_stream_is_rejected():
    class Chunks(httpx2.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(3):
                yield b"x" * (MAX_BYTES // 2)

    def handler(request):
        return httpx2.Response(200, stream=Chunks())

    async def check():
        async with limited(handler) as client:
            await client.get("https://provider.invalid/")

    with pytest.raises(PayloadLimitError):
        run(check())


def test_redirects_are_not_followed():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx2.Response(302, headers={"location": "https://elsewhere.invalid/"})

    async def check():
        async with limited(handler) as client:
            return await client.get("https://provider.invalid/")

    assert run(check()).status_code == 302
    assert calls == ["https://provider.invalid/"]


def test_missing_bearer_credential_fails_before_any_connection(monkeypatch):
    monkeypatch.delenv("WIRDI_TEST_ABSENT_TOKEN", raising=False)
    settings = ProviderSettings(
        provider_id="quran_mcp", enabled=True, bearer_token_env="WIRDI_TEST_ABSENT_TOKEN"
    )

    async def check():
        async with connect(settings, GatewaySettings(), catalog()["quran_mcp"]):
            raise AssertionError("must not connect")

    with pytest.raises(GatewayError) as error:
        run(check())
    assert error.value.issue.code == "AUTHENTICATION_FAILED"
    assert "WIRDI_TEST_ABSENT_TOKEN" not in str(error.value)


@pytest.mark.parametrize(
    ("status", "code", "retryable"),
    [
        (401, "AUTHENTICATION_FAILED", False),
        (403, "AUTHENTICATION_FAILED", False),
        (429, "RATE_LIMITED", True),
        (503, "PROVIDER_UNAVAILABLE", True),
        (404, "PROVIDER_UNAVAILABLE", False),
    ],
)
def test_http_status_classification_hides_provider_text(status, code, retryable):
    response = httpx2.Response(
        status, request=httpx2.Request("POST", "https://provider.invalid/"), text="SENSITIVE"
    )
    exc = httpx2.HTTPStatusError("SENSITIVE", request=response.request, response=response)
    error = classify(exc, "quran_mcp")
    assert (error.issue.code, error.issue.retryable) == (code, retryable)
    assert "SENSITIVE" not in error.issue.message


def test_tool_errors_are_typed_and_not_echoed():
    limited_result = CallToolResult(
        is_error=True, content=[TextContent(type="text", text="[rate_limited] SENSITIVE")]
    )
    with pytest.raises(GatewayError) as error:
        decode(limited_result)
    assert error.value.issue.code == "RATE_LIMITED" and error.value.issue.retryable
    other = CallToolResult(is_error=True, content=[TextContent(type="text", text="SENSITIVE")])
    with pytest.raises(GatewayError) as error:
        decode(other)
    assert error.value.issue.code == "PROVIDER_CALL_FAILED"
    assert "SENSITIVE" not in error.value.issue.message


def test_non_json_text_result_is_rejected():
    with pytest.raises(GatewayError) as error:
        decode(CallToolResult(content=[TextContent(type="text", text="not json")]))
    assert error.value.issue.code == "SCHEMA_MISMATCH"


class Client:
    def __init__(self):
        self.calls = []

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        raise AssertionError("must not be called")


def channel_for(tool):
    profile = {"admitted_tools": {"fetch_quran": {"signature_sha256": "0" * 64}}}
    client = Client()
    channel = Channel(client, profile, {"lock": asyncio.Lock(), "next": 0.0})
    channel.tools = {} if tool is None else {tool.name: tool}
    return channel, client


def test_unadmitted_absent_or_changed_tools_are_never_called():
    tool = Tool(
        name="fetch_quran",
        input_schema={"type": "object"},
        annotations=ToolAnnotations(read_only_hint=True),
    )
    for candidate, name in ((None, "fetch_quran"), (tool, "fetch_quran"), (tool, "other_tool")):
        channel, client = channel_for(candidate)
        with pytest.raises(GatewayError) as error:
            run(channel.call(name, {}))
        assert error.value.issue.code == "SCHEMA_MISMATCH"
        assert client.calls == []
