"""Administrator configuration; endpoints are fixed, opt-in and never caller-controlled."""

import json
from importlib.resources import files
from pathlib import Path

from pydantic import Field, ValidationError, model_validator

from wirdi_mcp.domain.models import ContractModel
from wirdi_mcp.providers.models import GatewayError, ProviderId


def catalog() -> dict:
    return json.loads(files("wirdi_mcp.providers").joinpath("catalog.json").read_bytes())


class ProviderSettings(ContractModel):
    provider_id: ProviderId
    enabled: bool = False
    bearer_token_env: str | None = Field(default=None, pattern=r"^[A-Z_][A-Z0-9_]*$")


class GatewaySettings(ContractModel):
    providers: tuple[ProviderSettings, ...] = ()
    call_timeout_seconds: float = Field(default=8, ge=0.05, le=20)
    operation_timeout_seconds: float = Field(default=16, ge=0.1, le=30)
    total_timeout_seconds: float = Field(default=35, ge=0.1, le=60)
    retries: int = Field(default=1, strict=True, ge=0, le=1)

    @model_validator(mode="after")
    def unique(self):
        if len({p.provider_id for p in self.providers}) != len(self.providers):
            raise ValueError("Duplicate provider IDs")
        return self


def load_settings(path: Path | None) -> GatewaySettings:
    if path is None:
        return GatewaySettings()
    try:
        if not path.is_absolute():
            raise ValueError("absolute path required")
        with path.open("rb") as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError("configuration too large")
        return GatewaySettings.model_validate_json(raw)
    except (OSError, ValueError, ValidationError):
        raise GatewayError(
            "INVALID_CONFIG", "Provider configuration is missing or invalid"
        ) from None
