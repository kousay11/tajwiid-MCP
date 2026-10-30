"""Read-only dependency boundary implemented by the verified file adapter."""

from typing import Protocol

from wirdi_mcp.domain.models import Passage, PassageSelection


class QalounDataReader(Protocol):
    async def get_passage(self, selection: PassageSelection) -> Passage:
        """Validate against an audited manifest, verify hashes, and read exact bytes."""
        ...
