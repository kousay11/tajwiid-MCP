# Trimmed from the Wirdi AI application's schemas module for the wirdi-mcp snapshot.
# Only CamelModel, PassageReference and MappingOut are kept, copied without change; the
# application's other schemas are not part of this repository. MIT licence (see LICENSE).
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """The mobile app speaks camelCase; Python stays snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class PassageReference(CamelModel):
    edition_id: str
    surah: int
    from_ayah: int
    to_ayah: int


class MappingOut(CamelModel):
    qaloun_reference: PassageReference | None = None
    source_reference: list[PassageReference] = Field(default_factory=list)
    mapping_status: Literal["verified_equivalent", "verified_difference", "mapping_requires_review"]
    mapping_type: str
    source_provenance: dict = Field(default_factory=dict)
    requires_user_notice: bool = True
    user_notice: str | None = None
    components: list[dict] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
