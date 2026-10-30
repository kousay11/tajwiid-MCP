"""Official SDK request-scoped client sessions, bounded HTTP bodies and safe errors."""

import asyncio
import json
import os
import re
from contextlib import asynccontextmanager

import httpx2
from jsonschema import ValidationError as SchemaValidationError
from jsonschema.validators import validator_for
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import MCPError

from wirdi_mcp.providers.config import GatewaySettings, ProviderSettings
from wirdi_mcp.providers.models import GatewayError, canonical_hash, signature_schema

MAX_BYTES = 2 * 1024 * 1024


class PayloadLimitError(Exception):
    pass


class LimitedStream(httpx2.AsyncByteStream):
    def __init__(self, stream):
        self.stream = stream

    async def __aiter__(self):
        size = 0
        async for chunk in self.stream:
            size += len(chunk)
            if size > MAX_BYTES:
                raise PayloadLimitError()
            yield chunk

    async def aclose(self):
        await self.stream.aclose()


class LimitedTransport(httpx2.AsyncBaseTransport):
    def __init__(self):
        self.inner = httpx2.AsyncHTTPTransport(retries=0)

    async def handle_async_request(self, request):
        response = await self.inner.handle_async_request(request)
        if response.headers.get("content-encoding", "identity") != "identity":
            await response.aclose()
            raise GatewayError("SCHEMA_MISMATCH", "Compressed provider responses are unsupported")
        length = response.headers.get("content-length", "0")
        if length.isdecimal() and int(length) > MAX_BYTES:
            await response.aclose()
            raise PayloadLimitError()
        return httpx2.Response(
            response.status_code,
            headers=response.headers,
            stream=LimitedStream(response.stream),
            extensions=response.extensions,
        )

    async def aclose(self):
        await self.inner.aclose()


@asynccontextmanager
async def connect(settings: ProviderSettings, policy: GatewaySettings, profile: dict):
    headers = {"Accept-Encoding": "identity"}
    if settings.bearer_token_env:
        token = os.environ.get(settings.bearer_token_env)
        if not token:
            raise GatewayError(
                "AUTHENTICATION_FAILED", "Configured provider credential is unavailable"
            )
        headers["Authorization"] = "Bearer " + token
    async with httpx2.AsyncClient(
        headers=headers,
        transport=LimitedTransport(),
        follow_redirects=False,
        timeout=httpx2.Timeout(
            policy.call_timeout_seconds, connect=min(4, policy.call_timeout_seconds)
        ),
        trust_env=False,
    ) as http:
        transport = streamable_http_client(
            profile["endpoint"], http_client=http, max_sse_event_size=MAX_BYTES
        )
        async with Client(transport, read_timeout_seconds=policy.call_timeout_seconds) as client:
            yield client


def schema_signature(tool) -> str:
    return canonical_hash(
        signature_schema({"input": tool.input_schema, "output": tool.output_schema})
    )


def reject_external_refs(value):
    if isinstance(value, dict):
        if "$ref" in value and not value["$ref"].startswith("#"):
            raise GatewayError("SCHEMA_MISMATCH", "External JSON schema references are unsupported")
        for v in value.values():
            reject_external_refs(v)
    elif isinstance(value, list):
        for v in value:
            reject_external_refs(v)


def validate(value, schema):
    if schema is not None:
        reject_external_refs(schema)
        try:
            validator_for(schema)(schema).validate(value)
        except SchemaValidationError:
            raise GatewayError(
                "SCHEMA_MISMATCH", "Provider payload does not match its schema"
            ) from None


def decode(result):
    # The digest includes the original MCP response envelope, not a rewritten excerpt.
    raw = result.model_dump(mode="json", by_alias=True)
    encoded = json.dumps(raw, ensure_ascii=False, allow_nan=False).encode()
    if len(encoded) > MAX_BYTES:
        raise GatewayError("RESPONSE_TOO_LARGE", "Provider response exceeds its byte limit")
    if result.is_error:
        text = " ".join(b.text for b in result.content if b.type == "text")
        if "[rate_limited]" in text:
            raise GatewayError("RATE_LIMITED", "Provider rate limit reached", retryable=True)
        raise GatewayError("PROVIDER_CALL_FAILED", "Provider rejected the read-only call")
    if result.structured_content is not None:
        return result.structured_content, canonical_hash(raw)
    text = "\n".join(b.text for b in result.content if b.type == "text")
    try:

        def unique(pairs):
            out = {}
            for k, v in pairs:
                if k in out:
                    raise ValueError("Duplicate JSON key")
                out[k] = v
            return out

        data = json.loads(
            text,
            object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except (ValueError, TypeError):
        raise GatewayError("SCHEMA_MISMATCH", "Provider did not return a JSON payload") from None
    return data, canonical_hash(raw)


def classify(exc: Exception, provider_id):
    if isinstance(exc, GatewayError):
        return GatewayError(exc.issue.code, exc.issue.message, provider_id, exc.issue.retryable)
    if isinstance(exc, BaseExceptionGroup):
        leaves = [classify(e, provider_id) for e in exc.exceptions]
        specific = next((e for e in leaves if e.issue.code != "PROVIDER_UNAVAILABLE"), None)
        return specific or next((e for e in leaves if e.issue.retryable), leaves[0])
    if isinstance(exc, PayloadLimitError):
        return GatewayError(
            "RESPONSE_TOO_LARGE", "Provider response exceeds its byte limit", provider_id
        )
    if isinstance(exc, (TimeoutError, httpx2.TimeoutException)) or re.search(
        "timed out", str(exc), re.I
    ):
        return GatewayError("PROVIDER_TIMEOUT", "Provider operation timed out", provider_id, True)
    if isinstance(exc, httpx2.HTTPStatusError):
        code = exc.response.status_code
        if code in (401, 403):
            return GatewayError(
                "AUTHENTICATION_FAILED", "Provider authentication failed", provider_id
            )
        if code == 429:
            return GatewayError("RATE_LIMITED", "Provider rate limit reached", provider_id, True)
        return GatewayError(
            "PROVIDER_UNAVAILABLE", "Provider HTTP endpoint unavailable", provider_id, code >= 500
        )
    if isinstance(exc, MCPError) and exc.code == -32603:
        return GatewayError(
            "PROVIDER_UNAVAILABLE", "Provider reported an internal error", provider_id, True
        )
    return GatewayError(
        "PROVIDER_UNAVAILABLE",
        "Provider connection failed",
        provider_id,
        isinstance(exc, (OSError, httpx2.TransportError)),
    )


class Channel:
    def __init__(self, client, profile, pacer):
        self.client, self.profile, self.pacer = client, profile, pacer
        self.tools = {}

    async def discover(self):
        cursor, seen, tools = None, set(), {}
        for _ in range(8):
            result = await self.client.list_tools(cursor=cursor)
            for tool in result.tools:
                if tool.name in tools or len(tools) >= 128:
                    raise GatewayError("SCHEMA_MISMATCH", "Provider tool catalog is invalid")
                tools[tool.name] = tool
            cursor = result.next_cursor
            if cursor is None:
                self.tools = tools
                return tools
            if cursor in seen:
                break
            seen.add(cursor)
        raise GatewayError("SCHEMA_MISMATCH", "Provider discovery pagination is incomplete")

    async def call(self, name: str, args: dict, *, plain_text=False):
        tool = self.tools.get(name)
        if (
            tool is None
            or name not in self.profile["admitted_tools"]
            or schema_signature(tool) != self.profile["admitted_tools"][name]["signature_sha256"]
            or tool.annotations is None
            or tool.annotations.read_only_hint is not True
        ):
            raise GatewayError(
                "SCHEMA_MISMATCH", "Provider tool is absent, changed or not admitted"
            )
        validate(args, tool.input_schema)
        async with self.pacer["lock"]:
            delay = self.pacer["next"] - asyncio.get_running_loop().time()
            if delay > 0:
                await asyncio.sleep(delay)
            self.pacer["next"] = (
                asyncio.get_running_loop().time() + self.profile["min_interval_seconds"]
            )
            result = await self.client.call_tool(name, args)
        if plain_text and not result.is_error:
            if len(result.model_dump_json().encode()) > MAX_BYTES:
                raise GatewayError("RESPONSE_TOO_LARGE", "Provider response exceeds its byte limit")
            return None, canonical_hash(result.model_dump(mode="json"))
        payload, sha = decode(result)
        validate(payload, tool.output_schema)
        return payload, sha
