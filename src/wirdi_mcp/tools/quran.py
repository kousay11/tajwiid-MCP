"""Implemented Phase 2 read-only tools with typed success/error envelopes."""

from typing import Annotated

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.domain.models import (
    Failure,
    NonEmpty,
    Passage,
    PassageSelection,
    Provenance,
    SourceMapping,
    Success,
)
from wirdi_mcp.mapping.adapter import WirdiSourceMappingAdapter
from wirdi_mcp.quran.source import TARIQ_WARNING, PublicSourceRepository, QalounFileAdapter
from wirdi_mcp.tools.contracts import MappingToolResponse, PassageToolResponse


def tool_result(payload: Success | Failure) -> CallToolResult:
    return CallToolResult(
        is_error=isinstance(payload, Failure),
        structured_content=payload.model_dump(mode="json"),
        content=[TextContent(type="text", text=payload.model_dump_json())],
    )


def register_quran_tools(server: MCPServer, repository: PublicSourceRepository) -> None:
    reader = QalounFileAdapter(repository)
    mapper = WirdiSourceMappingAdapter(repository)
    annotations = ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )

    @server.tool(annotations=annotations)
    async def get_qaloun_passage(
        selection: PassageSelection,
    ) -> Annotated[CallToolResult, PassageToolResponse]:
        """Read unchanged Qaloun ayat and verified page spans from checksum-pinned source files."""
        try:
            passage = await reader.get_passage(selection)
            pagination = repository.manifest["pagination_path"]
            payload = Success[Passage](
                data=passage,
                validation_status="machine_checked",
                warnings=(TARIQ_WARNING,),
                provenance=(
                    repository.provenance(
                        "qalun",
                        f"{selection.start.surah}:{selection.start.ayah}-{selection.end_ayah}",
                    ),
                    Provenance(
                        origin_id="wirdi-ai:qaloun-pagination",
                        origin_version=repository.manifest["manifest_version"],
                        content_sha256=repository.manifest["artifacts"][pagination],
                        citations=(
                            repository.audit_citation(
                                "docs/qaloun-pagination-validation.md", "559-page edition audit"
                            ),
                        ),
                    ),
                ),
            )
            return tool_result(payload)
        except KnowledgeError as exc:
            return tool_result(Failure(error=exc.error))

    @server.tool(annotations=annotations)
    async def resolve_source_mapping(
        selection: PassageSelection,
        target_corpus_id: NonEmpty,
        target_corpus_version: NonEmpty,
        target_numbering_system: NonEmpty,
    ) -> Annotated[CallToolResult, MappingToolResponse]:
        """Reuse the pinned mapper; review-required ranges are unsafe for source retrieval."""
        try:
            mapping = await mapper.resolve(
                selection,
                target_corpus_id,
                target_corpus_version,
                target_numbering_system,
            )
            warnings = (TARIQ_WARNING,)
            if not mapping.safe_for_source_retrieval:
                warnings += (
                    "Mapping requires review. Candidate ranges must not be used for retrieval.",
                )
            return tool_result(
                Success[SourceMapping](
                    data=mapping,
                    validation_status=mapping.validation_status,
                    warnings=warnings,
                    provenance=(
                        repository.provenance("qalun", "Canonical Qaloun source records and links"),
                        repository.provenance("hafs", "Internal target source records"),
                        Provenance(
                            origin_id="wirdi-ai:source-mapping",
                            origin_version=mapping.mapping_version,
                            content_sha256=mapping.mapping_artifact_sha256,
                            citations=mapping.evidence,
                        ),
                    ),
                )
            )
        except KnowledgeError as exc:
            return tool_result(Failure(error=exc.error))
