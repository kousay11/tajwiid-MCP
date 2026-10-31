"""Read-only access to locally placed source-book pages, with a hash check on every read.

Book text is never bundled: licence status of every source is unknown, so the page files
(`knowledge/sources/<edition>/pages.jsonl` and `pages_manifest.json`) are git-ignored and
only exist where a user built them from their own copy. A missing store fails closed with
DATA_UNAVAILABLE and a changed byte fails with INTEGRITY_FAILURE.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.knowledge.registry import RuleRegistry, digest

MAX_PAGES_PER_CALL = 5
MAX_STORE_BYTES = 32 * 1024 * 1024
MAX_PAGE_CHARS = 20_000
EDITION_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_BIDI = dict.fromkeys(
    [*range(0x202A, 0x202F), 0x200E, 0x200F, *range(0x2066, 0x206A), 0x0640], None
)
_DIACRITICS = dict.fromkeys([*range(0x064B, 0x0660), 0x0670, *range(0x06D6, 0x06EE)], None)
_FOLD = str.maketrans("أإآٱىةؤئ", "اااايهوي")


def normalize_arabic(text: str) -> str:
    """Lossy search form: strips marks and bidi controls, folds letter variants and the
    inverted lam-alef ligature order that the extractor produces for book A.
    Used to match queries only; never shown as source text."""
    text = unicodedata.normalize("NFKC", text).translate(_BIDI).translate(_DIACRITICS)
    text = text.replace("هللا", "الله").translate(_FOLD)
    return " ".join(text.replace("لا", "ال").split())


@dataclass(frozen=True)
class StoredPage:
    edition_id: str
    pdf_page: int
    printed_page: str
    text: str
    text_sha256: str
    text_quality: str


class PageStore:
    def __init__(self, registry: RuleRegistry):
        self.registry = registry

    def _edition(self, edition_id: str) -> dict:
        if not EDITION_ID.fullmatch(edition_id):
            raise KnowledgeError("NOT_FOUND", "Unknown source edition")
        edition = self.registry.editions().get(edition_id)
        if edition is None:
            raise KnowledgeError("NOT_FOUND", "Unknown source edition")
        return edition

    def load(self, edition_id: str) -> tuple[dict, dict[int, StoredPage]]:
        edition = self._edition(edition_id)
        base = f"sources/{edition_id}/"
        try:
            store = json.loads(self.registry._read(base + "pages_manifest.json"))
        except (ValueError, TypeError):
            raise KnowledgeError("INTEGRITY_FAILURE", "Page store manifest is malformed") from None
        raw = self.registry._read(base + "pages.jsonl")
        if len(raw) > MAX_STORE_BYTES or digest(raw) != store.get("pages_sha256"):
            raise KnowledgeError("INTEGRITY_FAILURE", "Page store checksum mismatch")
        pages: dict[int, StoredPage] = {}
        try:
            for line in raw.decode("utf-8").splitlines():
                row = json.loads(line)
                pdf_page = int(row["pdf_page"])
                if (
                    not 1 <= pdf_page <= edition["page_count"]
                    or pdf_page in pages
                    or len(row["text"]) > MAX_PAGE_CHARS
                ):
                    raise ValueError
                pages[pdf_page] = StoredPage(
                    edition_id,
                    pdf_page,
                    str(pdf_page - edition["page_label_offset"]),
                    row["text"],
                    digest(row["text"].encode("utf-8")),
                    store["text_quality"],
                )
        except (ValueError, KeyError, TypeError):
            raise KnowledgeError("INTEGRITY_FAILURE", "Page store is malformed") from None
        return edition, pages

    def get_pages(self, edition_id: str, first_printed: int, last_printed: int) -> list[StoredPage]:
        if not 1 <= last_printed - first_printed + 1 <= MAX_PAGES_PER_CALL:
            raise KnowledgeError(
                "INVALID_REFERENCE", f"Request 1 to {MAX_PAGES_PER_CALL} consecutive pages"
            )
        edition, pages = self.load(edition_id)
        offset = edition["page_label_offset"]
        wanted = range(first_printed + offset, last_printed + offset + 1)
        missing = [p for p in wanted if p not in pages]
        if missing:
            raise KnowledgeError("NOT_FOUND", "A requested page is not in the local store")
        return [pages[p] for p in wanted]

    def search(
        self, query: str, edition_ids: tuple[str, ...], limit: int
    ) -> list[tuple[StoredPage, int, str]]:
        needle = normalize_arabic(query)
        if len(needle) < 2:
            raise KnowledgeError("INVALID_REFERENCE", "The query is too short after normalization")
        hits: list[tuple[StoredPage, int, str]] = []
        for edition_id in edition_ids:
            _edition, pages = self.load(edition_id)
            for pdf_page in sorted(pages):
                page = pages[pdf_page]
                folded = normalize_arabic(page.text)
                count = folded.count(needle)
                if count:
                    at = folded.index(needle)
                    snippet = folded[max(0, at - 40) : at + len(needle) + 40]
                    hits.append((page, count, snippet))
                    if len(hits) >= limit:
                        return hits
        return hits


def local_editions_with_store(root: Path | None) -> tuple[str, ...]:
    """Edition ids that have a page store directory; existence only, not integrity."""
    if root is None:
        return ()
    base = root / "sources"
    if not base.is_dir():
        return ()
    return tuple(sorted(p.parent.name for p in base.glob("*/pages.jsonl")))
