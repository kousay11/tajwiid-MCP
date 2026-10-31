"""Small environment configuration; no network, filesystem data, or secret loading."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


def default_knowledge_root() -> Path | None:
    """The repository's own `knowledge/` directory when running from a source checkout."""
    candidate = Path(__file__).resolve().parents[2] / "knowledge"
    return candidate if (candidate / "rules" / "manifest.json").is_file() else None


@dataclass(frozen=True)
class Settings:
    log_level: str = "INFO"
    wirdi_ai_root: Path | None = None
    knowledge_root: Path | None = None
    # "bundled": the snapshot shipped with the package (default); "external": a Wirdi AI
    # checkout given by WIRDI_AI_ROOT; "none": no Quran source (tests of the typed failure).
    quran_source: str = "bundled"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if env is None else env
        level = values.get("WIRDI_MCP_LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("WIRDI_MCP_LOG_LEVEL must be a supported logging level")
        root = values.get("WIRDI_AI_ROOT", "")
        if root and not Path(root).is_absolute():
            raise ValueError("WIRDI_AI_ROOT must be an absolute path")
        source = values.get("WIRDI_QURAN_SOURCE", "")
        if source not in {"", "none"}:
            raise ValueError("WIRDI_QURAN_SOURCE must be empty or 'none'")
        knowledge = values.get("WIRDI_KNOWLEDGE_ROOT", "")
        if knowledge and not Path(knowledge).is_absolute():
            raise ValueError("WIRDI_KNOWLEDGE_ROOT must be an absolute path")
        return cls(
            log_level=level,
            wirdi_ai_root=Path(root) if root else None,
            knowledge_root=Path(knowledge) if knowledge else default_knowledge_root(),
            quran_source="none" if source == "none" else ("external" if root else "bundled"),
        )
