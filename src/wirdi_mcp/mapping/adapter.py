"""Read-only reuse of the existing verified source-boundary resolver."""

import asyncio
from typing import Protocol

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.domain.models import NonEmpty, PassageSelection, SourceMapping
from wirdi_mcp.mapping.bridge import ReadOnlyAuthorityView, bind_authority
from wirdi_mcp.quran.source import PublicSourceRepository


class SourceMappingAuthority(Protocol):
    async def resolve(
        self,
        selection: PassageSelection,
        target_corpus_id: NonEmpty,
        target_corpus_version: NonEmpty,
        target_numbering_system: NonEmpty,
    ) -> SourceMapping:
        """Delegate to the versioned existing authority; reject ambiguous boundaries."""
        ...


class WirdiSourceMappingAdapter:
    def __init__(self, repository: PublicSourceRepository):
        self.repository = repository

    def resolve_sync(
        self,
        selection: PassageSelection,
        target_corpus_id: str,
        target_corpus_version: str,
        target_numbering_system: str,
    ) -> SourceMapping:
        repo = self.repository
        repo.validate_selection(selection)
        target = repo.manifest["editions"]["hafs"]
        if (target_corpus_id, target_corpus_version, target_numbering_system) != (
            target["corpus_id"],
            target["version"],
            target["numbering_system"],
        ):
            raise KnowledgeError(
                "UNSUPPORTED_VERSION", "Unsupported target corpus, version or numbering"
            )
        rows = {eid: repo.load_edition(eid) for eid in ("qalun", "hafs")}
        # No dependency on pagination: boundary mapping and printed pages are separate.
        repo.read_artifact("docs/reader-corrections-report.md")
        mapper_path = "backend/app/tadabbur/mapping.py"
        resolver = bind_authority(
            repo.read_artifact(mapper_path),
            repo.read_artifact("backend/app/tadabbur/arabic.py"),
            repo.read_artifact("backend/app/schemas.py"),
        )
        editions = {
            eid: {
                "source": meta["source"],
                "license": repo.manifest["license"],
                "source_checksum": repo.manifest["artifacts"][meta["path"]],
                "text_checksum": meta["text_sha256"],
            }
            for eid, meta in repo.manifest["editions"].items()
        }
        view = ReadOnlyAuthorityView(rows, editions)
        selected = view.select_qaloun(
            selection.start.surah, selection.start.ayah, selection.end_ayah
        )
        native = resolver(view, selected, "qalun", selection.start.surah).model_dump()
        safe = native["mapping_status"] in {"verified_equivalent", "verified_difference"}
        return SourceMapping(
            qaloun_reference=selection,
            source_reference=tuple(
                {
                    "start": repo.reference("hafs", r["surah"], r["from_ayah"]),
                    "end_ayah": r["to_ayah"],
                }
                for r in native["source_reference"]
            ),
            mapping_status=native["mapping_status"],
            mapping_type=native["mapping_type"],
            mapping_version="linked_components_and_exact_orthographic_skeleton_v1",
            mapping_artifact_sha256=repo.manifest["artifacts"][mapper_path],
            components=tuple(native["components"]),
            source_provenance=native["source_provenance"],
            requires_user_notice=native["requires_user_notice"],
            user_notice=native["user_notice"],
            reasons=tuple(native["reasons"]),
            safe_for_source_retrieval=safe,
            validation_status="machine_checked" if safe else "unreviewed",
            evidence=(
                repo.citation(
                    "qalun", f"{selection.start.surah}:{selection.start.ayah}-{selection.end_ayah}"
                ),
                repo.audit_citation(
                    "docs/reader-corrections-report.md", "Mapping validation limits"
                ),
            ),
        )

    async def resolve(
        self,
        selection: PassageSelection,
        target_corpus_id: NonEmpty,
        target_corpus_version: NonEmpty,
        target_numbering_system: NonEmpty,
    ) -> SourceMapping:
        return await asyncio.to_thread(
            self.resolve_sync,
            selection,
            target_corpus_id,
            target_corpus_version,
            target_numbering_system,
        )
