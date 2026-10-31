"""Hash-pinned reads of existing Wirdi AI public source artifacts."""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.domain.models import (
    Ayah,
    Citation,
    Passage,
    PassageSelection,
    Provenance,
    QalounReference,
    QuranReference,
)

TARIQ_WARNING = (
    "The inspected corpus identifies Qaloun but does not independently attest Abu Nashit; "
    "tariq is unspecified. No path-specific Tajwid claim is supported."
)


SNAPSHOT_ROOT = Path(__file__).resolve().parent / "snapshot"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_manifest() -> dict:
    return json.loads(files("wirdi_mcp.quran").joinpath("source_manifest.json").read_bytes())


@dataclass(frozen=True)
class SourceAyah:
    surah: int
    number: int
    text: str
    links: tuple[int, ...]


class PublicSourceRepository:
    """No database, importer, writes or alternate source lookup. No on-disk cache.

    `mode` says which pinned bytes are expected. `external` is a Wirdi AI checkout, whose files
    are the originals. `bundled` is the snapshot shipped with this package: six files are the
    same bytes, four (the trimmed schemas and three public notes) differ and have their own
    pinned hashes in the manifest's `bundled` section.
    """

    def __init__(self, root: Path | None, mode: str = "external"):
        self.root = root
        self.mode = mode
        self.manifest = source_manifest()
        bundled = self.manifest.pop("bundled", {})
        if mode == "bundled":
            self.manifest["artifacts"] = {**self.manifest["artifacts"], **bundled["artifacts"]}

    @classmethod
    def bundled(cls) -> "PublicSourceRepository":
        return cls(SNAPSHOT_ROOT, "bundled")

    @property
    def source(self) -> str:
        if self.root is None:
            return "none"
        return "bundled" if self.mode == "bundled" else "external"

    def read_artifact(self, relative: str) -> bytes:
        if self.root is None:
            raise KnowledgeError("DATA_UNAVAILABLE", "Public Quran source root is not configured")
        try:
            root = self.root.resolve(strict=True)
            path = (root / relative).resolve(strict=True)
            if not path.is_relative_to(root):
                raise KnowledgeError(
                    "INTEGRITY_FAILURE", "Source artifact escapes its configured root"
                )
            with path.open("rb") as stream:
                data = stream.read(16 * 1024 * 1024 + 1)
        except (OSError, RuntimeError):
            raise KnowledgeError(
                "DATA_UNAVAILABLE", "A required public source artifact is unreadable"
            ) from None
        if digest(data) != self.manifest["artifacts"][relative]:
            raise KnowledgeError("INTEGRITY_FAILURE", "Public source artifact checksum mismatch")
        return data

    def load_edition(self, edition: str) -> tuple[SourceAyah, ...]:
        meta = self.manifest["editions"][edition]
        data = json.loads(self.read_artifact(meta["path"]))
        if set(data) != {str(s) for s in range(1, 115)}:
            raise KnowledgeError("INTEGRITY_FAILURE", "Source surah identity mismatch")
        rows = []
        for surah in range(1, 115):
            verses = data[str(surah)]
            if len(verses) != meta["surah_counts"][surah - 1]:
                raise KnowledgeError("INTEGRITY_FAILURE", "Source verse counts mismatch")
            for number, verse in enumerate(verses, 1):
                if (
                    type(verse["chapter"]) is not int
                    or verse["chapter"] != surah
                    or type(verse["verse"]) is not int
                    or verse["verse"] != number
                    or not isinstance(verse["text"], str)
                    or not verse["text"].strip()
                    or not isinstance(verse["number_in_hafs"], list)
                    or any(type(n) is not int for n in verse["number_in_hafs"])
                ):
                    raise KnowledgeError("INTEGRITY_FAILURE", "Source record structure mismatch")
                rows.append(
                    SourceAyah(surah, number, verse["text"], tuple(verse["number_in_hafs"]))
                )
        if (
            len(rows) != meta["ayah_count"]
            or digest("\n".join(r.text for r in rows).encode("utf-8")) != meta["text_sha256"]
        ):
            raise KnowledgeError("INTEGRITY_FAILURE", "Ordered Quran text checksum mismatch")
        return tuple(rows)

    def validate_selection(self, selection: PassageSelection) -> None:
        start = selection.start
        meta = self.manifest["editions"]["qalun"]
        if start.corpus_id != meta["corpus_id"] or start.corpus_version != meta["version"]:
            raise KnowledgeError(
                "UNSUPPORTED_VERSION", "Unsupported Qaloun corpus identity or version"
            )
        if start.numbering_system != meta["numbering_system"]:
            raise KnowledgeError(
                "INVALID_REFERENCE", "Reference numbering system does not match the corpus"
            )
        if start.tariq != meta["tariq"]:
            raise KnowledgeError(
                "UNSUPPORTED_CONTEXT", "This source does not attest the requested tariq"
            )
        if selection.end_ayah > meta["surah_counts"][start.surah - 1]:
            raise KnowledgeError("INVALID_REFERENCE", "Ayah is outside the Qaloun surah bounds")

    def reference(self, edition: str, surah: int, ayah: int) -> QuranReference:
        meta = self.manifest["editions"][edition]
        model = QalounReference if edition == "qalun" else QuranReference
        return model(
            corpus_id=meta["corpus_id"],
            corpus_version=meta["version"],
            numbering_system=meta["numbering_system"],
            riwaya=meta["riwaya"],
            tariq=meta["tariq"],
            surah=surah,
            ayah=ayah,
        )

    def citation(self, edition: str, locator: str) -> Citation:
        meta = self.manifest["editions"][edition]
        return Citation(
            source_id="quranpedia:" + edition,
            edition_id=meta["corpus_id"],
            title="KFGQPC Qaloun via Qur'anpedia"
            if edition == "qalun"
            else "QPC Hafs via Qur'anpedia",
            responsible_party="Qur'anpedia.net; distribution: risan/quran-json",
            publication="Source checkout " + self.manifest["upstream_revision"],
            locator=locator,
            riwaya=meta["riwaya"],
            tariq=meta["tariq"],
            provenance_version=meta["version"],
            validation_status="machine_checked",
            uri="https://github.com/risan/quran-json/tree/" + self.manifest["upstream_revision"],
        )

    def provenance(self, edition: str, locator: str) -> Provenance:
        meta = self.manifest["editions"][edition]
        return Provenance(
            origin_id=meta["corpus_id"],
            origin_version=meta["version"],
            content_sha256=self.manifest["artifacts"][meta["path"]],
            citations=(self.citation(edition, locator),),
        )

    def audit_citation(self, path: str, locator: str) -> Citation:
        bundled = self.mode == "bundled"
        return Citation(
            source_id="wirdi-mcp:snapshot-notes" if bundled else "wirdi-ai:audit",
            edition_id=self.manifest["manifest_version"],
            title=path.rsplit("/", 1)[-1],
            responsible_party="wirdi-mcp snapshot" if bundled else "Wirdi AI project audit",
            publication=(
                "Public note bundled with wirdi-mcp"
                if bundled
                else "Existing local project audit, 2026-10-29"
            ),
            locator=locator,
            riwaya="qaloun",
            tariq="unspecified",
            provenance_version="sha256:" + self.manifest["artifacts"][path],
            validation_status="machine_checked",
        )

    def load_pages(self) -> tuple[tuple[int, int], ...]:
        doc = json.loads(self.read_artifact(self.manifest["pagination_path"]))
        pages = doc["verse_pages"]
        if (
            doc["edition_id"] != "qalun"
            or doc["page_count"] != 559
            or doc["verse_count"] != 6214
            or len(pages) != 6214
            or doc["reference"] != self.manifest["pagination_reference"]
            or doc["map_sha256"] != self.manifest["pagination_sha256"]
            or digest(json.dumps(pages).encode()) != self.manifest["pagination_sha256"]
            or any(
                len(p) != 2 or any(type(n) is not int for n in p) or not 1 <= p[0] <= p[1] <= 559
                for p in pages
            )
            or pages[0][0] != 1
            or pages[-1][1] != 559
            or any(a[0] > b[0] or a[1] > b[1] for a, b in zip(pages, pages[1:], strict=False))
        ):
            raise KnowledgeError(
                "INTEGRITY_FAILURE", "Verified pagination identity or structure mismatch"
            )
        for path in ("docs/qaloun-pagination-validation.md", "docs/day2-final-validation.md"):
            self.read_artifact(path)
        return tuple(tuple(p) for p in pages)


class QalounFileAdapter:
    def __init__(self, repository: PublicSourceRepository):
        self.repository = repository

    def read_passage(self, selection: PassageSelection) -> Passage:
        repo = self.repository
        repo.validate_selection(selection)
        rows = repo.load_edition("qalun")
        pages = repo.load_pages()
        ayat = tuple(
            Ayah(
                reference=repo.reference("qalun", row.surah, row.number),
                text=row.text,
                text_sha256=digest(row.text.encode("utf-8")),
                provenance=repo.provenance("qalun", f"{row.surah}:{row.number}"),
                page_start=pages[index][0],
                page_end=pages[index][1],
            )
            for index, row in enumerate(rows)
            if row.surah == selection.start.surah
            and selection.start.ayah <= row.number <= selection.end_ayah
        )
        meta = repo.manifest["editions"]["qalun"]
        return Passage(
            selection=selection,
            ayat=ayat,
            snapshot_sha256=repo.manifest["artifacts"][meta["path"]],
            corpus_text_sha256=meta["text_sha256"],
            pagination_sha256=repo.manifest["pagination_sha256"],
            pagination_status="verified_against_edition",
            tariq_attestation=repo.manifest["tariq_attestation"],
        )

    async def get_passage(self, selection: PassageSelection) -> Passage:
        return await asyncio.to_thread(self.read_passage, selection)
