"""Optional gateway: lazy sessions, admitted reads, mapping guard and fallback."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.mapping.adapter import WirdiSourceMappingAdapter
from wirdi_mcp.mapping.bridge import bind_authority
from wirdi_mcp.providers.adapters import ADAPTERS, invalid_payload
from wirdi_mcp.providers.config import GatewaySettings, catalog, load_settings
from wirdi_mcp.providers.models import (
    CapabilitiesResult,
    Capability,
    GatewayError,
    ProviderAttempt,
    ProviderState,
    SearchRequest,
    SearchResult,
)
from wirdi_mcp.providers.transport import Channel, classify, connect, schema_signature
from wirdi_mcp.quran.source import PublicSourceRepository


class ProviderGateway:
    def __init__(
        self,
        repository: PublicSourceRepository,
        config_path: Path | None = None,
        *,
        connector=connect,
        settings: GatewaySettings | None = None,
    ):
        self.repository, self.config_path = repository, config_path
        self.connector, self.explicit_settings = connector, settings
        self.catalog = catalog()
        self.states = {}
        self._semaphore = asyncio.Semaphore(2)
        self._pacers = {pid: {"lock": asyncio.Lock(), "next": 0.0} for pid in self.catalog}

    def settings(self):
        return self.explicit_settings or load_settings(self.config_path)

    async def operation(self, provider, policy, action):
        profile = self.catalog[provider.provider_id]
        async with self._semaphore:
            try:
                async with asyncio.timeout(policy.operation_timeout_seconds):
                    for attempt in range(policy.retries + 1):
                        try:
                            async with self.connector(provider, policy, profile) as client:
                                channel = Channel(
                                    client, profile, self._pacers[provider.provider_id]
                                )
                                await channel.discover()
                                return await action(channel)
                        except Exception as exc:
                            error = classify(invalid_payload(exc), provider.provider_id)
                            if not error.issue.retryable or attempt == policy.retries:
                                raise error from None
                            await asyncio.sleep(1.1 if error.issue.code == "RATE_LIMITED" else 0.1)
            except TimeoutError:
                raise GatewayError(
                    "PROVIDER_TIMEOUT",
                    "Provider operation deadline exceeded",
                    provider.provider_id,
                    True,
                ) from None

    def provider_state(self, pid, enabled):
        if not enabled:
            return ProviderState(
                provider_id=pid,
                enabled=False,
                status="disabled",
                source_id=self.catalog[pid]["source_id"],
            )
        return self.states.get(pid) or ProviderState(
            provider_id=pid,
            enabled=True,
            status="not_discovered",
            source_id=self.catalog[pid]["source_id"],
        )

    async def capabilities(self, provider_id=None, refresh=False):
        policy = self.settings()
        enabled = {p.provider_id: p for p in policy.providers if p.enabled}
        ids = [provider_id] if provider_id else list(self.catalog)
        if any(pid not in self.catalog for pid in ids):
            raise GatewayError("NOT_FOUND", "Provider is not configured in the audited catalog")

        async def discover(pid):
            profile = self.catalog[pid]

            async def action(channel):
                capabilities = []
                for tool in channel.tools.values():
                    signature = schema_signature(tool)
                    admitted = (
                        tool.name in profile["admitted_tools"]
                        and signature == profile["admitted_tools"][tool.name]["signature_sha256"]
                        and tool.annotations is not None
                        and tool.annotations.read_only_hint is True
                    )
                    capabilities.append(
                        Capability(
                            provider_id=pid,
                            tool_name=tool.name,
                            input_schema=tool.input_schema,
                            output_schema=tool.output_schema,
                            signature_sha256=signature,
                            admitted=admitted,
                            evidence_level="runtime_discovered",
                            categories=tuple(
                                profile["admitted_tools"].get(tool.name, {}).get("categories", ())
                            ),
                        )
                    )
                return ProviderState(
                    provider_id=pid,
                    enabled=True,
                    status="ready",
                    source_id=profile["source_id"],
                    tools=tuple(capabilities),
                    observed_at=datetime.now(UTC),
                )

            try:
                self.states[pid] = await self.operation(enabled[pid], policy, action)
            except GatewayError as exc:
                self.states[pid] = ProviderState(
                    provider_id=pid,
                    enabled=True,
                    status="unavailable",
                    source_id=profile["source_id"],
                    issues=(exc.issue,),
                    observed_at=datetime.now(UTC),
                )

        if refresh:
            try:
                async with asyncio.timeout(policy.total_timeout_seconds):
                    await asyncio.gather(*(discover(pid) for pid in ids if pid in enabled))
            except TimeoutError:
                raise GatewayError(
                    "PROVIDER_TIMEOUT", "Gateway discovery deadline exceeded", retryable=True
                ) from None
        return CapabilitiesResult(
            providers=tuple(self.provider_state(pid, pid in enabled) for pid in ids)
        )

    async def prepare_scope(self, request):
        if request.selection is None:
            return None, None, None
        source = request.source_identity
        try:
            mapping = await WirdiSourceMappingAdapter(self.repository).resolve(
                request.selection,
                source.corpus_id,
                source.corpus_version,
                source.numbering_system,
            )
            if not mapping.safe_for_source_retrieval:
                raise GatewayError(
                    "AMBIGUOUS_MAPPING",
                    "Review-required mappings cannot authorize external retrieval",
                )
            refs = {
                (r.start.surah, n)
                for r in mapping.source_reference
                for n in range(r.start.ayah, r.end_ayah + 1)
            }
            if len(refs) > 8:
                raise GatewayError(
                    "UNSUPPORTED_CAPABILITY",
                    "Passage-scoped gateway requests support at most eight source ayat",
                )
            rows = await asyncio.to_thread(self.repository.load_edition, "hafs")
            expected = {(r.surah, r.number): r.text for r in rows if (r.surah, r.number) in refs}
            repo = self.repository
            resolver = bind_authority(
                repo.read_artifact("backend/app/tadabbur/mapping.py"),
                repo.read_artifact("backend/app/tadabbur/arabic.py"),
                repo.read_artifact("backend/app/schemas.py"),
            )
            return mapping, expected, resolver.__globals__["skeleton"]
        except KnowledgeError as exc:
            raise GatewayError(exc.error.code, exc.error.message) from None

    async def search(self, request: SearchRequest):
        policy = self.settings()
        # Admit the Qaloun mapping before discovery or any external call.
        mapping, expected, skeleton = await self.prepare_scope(request)
        configured = {p.provider_id: p for p in policy.providers if p.enabled}
        ids = request.provider_ids or tuple(configured)
        if not ids:
            raise GatewayError("PROVIDER_UNAVAILABLE", "No external providers are enabled")
        issues, attempts, warnings = [], [], []
        had_empty, had_partial = False, False
        try:
            async with asyncio.timeout(policy.total_timeout_seconds):
                for pid in ids:
                    try:
                        if pid not in configured:
                            raise GatewayError(
                                "PROVIDER_UNAVAILABLE", "Requested provider is disabled", pid
                            )
                        if pid not in ADAPTERS:
                            raise GatewayError(
                                "UNSUPPORTED_CAPABILITY",
                                "Provider has no demonstrated scholarly search adapter",
                                pid,
                            )
                        if request.source_identity is not None and (
                            request.source_identity.provider_sources.get(pid)
                            != self.catalog[pid]["source_id"]
                        ):
                            raise GatewayError(
                                "UNSUPPORTED_VERSION",
                                "Explicit provider source identity is missing or incompatible",
                                pid,
                            )
                        adapter = ADAPTERS[pid]()

                        async def action(channel, adapter=adapter):
                            if hasattr(adapter, "prerequisite"):
                                await adapter.prerequisite(channel)
                            if expected is not None:
                                observed = await adapter.source_texts(channel, set(expected))
                                if set(observed) != set(expected) or any(
                                    skeleton(observed[k]) != skeleton(expected[k]) for k in expected
                                ):
                                    raise GatewayError(
                                        "INCOMPATIBLE_RIWAYA",
                                        "Provider boundaries do not match the mapping target",
                                    )
                            return await adapter.search(
                                channel, request, None if expected is None else set(expected)
                            )

                        batch = await self.operation(configured[pid], policy, action)
                        attempts.append(
                            ProviderAttempt(
                                provider_id=pid, outcome="success" if batch.hits else "empty"
                            )
                        )
                        warnings.extend(batch.warnings)
                        had_partial = had_partial or batch.partial
                        if not batch.hits:
                            had_empty = True
                            continue
                        hits = tuple(
                            h.model_copy(
                                update={
                                    "compatibility": "mapped_boundaries_checked",
                                    "mapping_sha256": mapping.mapping_artifact_sha256,
                                }
                            )
                            if mapping is not None
                            else h
                            for h in batch.hits
                        )
                        return SearchResult(
                            hits=hits,
                            partial=bool(issues) or had_partial,
                            attempts=tuple(attempts),
                            issues=tuple(issues),
                            warnings=tuple(warnings),
                            mapping_status=None if mapping is None else mapping.mapping_status,
                        )
                    except GatewayError as exc:
                        issues.append(exc.issue)
                        attempts.append(ProviderAttempt(provider_id=pid, outcome="failed"))
        except TimeoutError:
            issues.append(
                GatewayError(
                    "PROVIDER_TIMEOUT", "Gateway search deadline exceeded", retryable=True
                ).issue
            )
        if had_empty:
            return SearchResult(
                hits=(),
                partial=bool(issues) or had_partial,
                attempts=tuple(attempts),
                issues=tuple(issues),
                warnings=tuple(warnings),
                mapping_status=None if mapping is None else mapping.mapping_status,
            )
        error = GatewayError(
            "PROVIDER_UNAVAILABLE", "No compatible provider returned usable scholarly evidence"
        )
        error.issues = tuple(issues)
        raise error
