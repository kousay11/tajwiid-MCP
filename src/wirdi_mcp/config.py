"""Small environment configuration; no network, filesystem data, or secret loading."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    log_level: str = "INFO"
    wirdi_ai_root: Path | None = None
    provider_config: Path | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if env is None else env
        level = values.get("WIRDI_MCP_LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("WIRDI_MCP_LOG_LEVEL must be a supported logging level")
        root = values.get("WIRDI_AI_ROOT", "")
        if root and not Path(root).is_absolute():
            raise ValueError("WIRDI_AI_ROOT must be an absolute path")
        provider_config = values.get("WIRDI_MCP_PROVIDER_CONFIG", "")
        return cls(
            log_level=level,
            wirdi_ai_root=Path(root) if root else None,
            provider_config=Path(provider_config) if provider_config else None,
        )
