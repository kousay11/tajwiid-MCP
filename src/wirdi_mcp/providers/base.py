"""Small adapter interface; MCP lifecycle and admission belong to the gateway."""

from dataclasses import dataclass
from typing import Protocol

from wirdi_mcp.providers.models import ExternalHit, SearchRequest
from wirdi_mcp.providers.transport import Channel


@dataclass(frozen=True)
class SearchBatch:
    hits: tuple[ExternalHit, ...]
    partial: bool = False
    warnings: tuple[str, ...] = ()


class ProviderAdapter(Protocol):
    async def source_texts(self, channel: Channel, refs: set[tuple[int, int]]) -> dict: ...

    async def search(
        self, channel: Channel, request: SearchRequest, refs: set[tuple[int, int]] | None
    ) -> SearchBatch: ...
