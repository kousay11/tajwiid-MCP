import hashlib
import json

import pytest

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.knowledge.pages import PageStore, normalize_arabic
from wirdi_mcp.knowledge.registry import RuleRegistry

SENTINEL_PAGES = {1: "SENTINEL alpha", 2: "SENTINEL beta", 3: "SENTINEL gamma"}


def build_store(root, edition="book-a-2010", pages=SENTINEL_PAGES):
    store = root / "sources" / edition
    store.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps({"pdf_page": p, "text": t}) + "\n" for p, t in pages.items())
    (store / "pages.jsonl").write_bytes(body.encode())
    manifest = {
        "edition_id": edition,
        "page_count": len(pages),
        "pages_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "text_quality": "synthetic",
    }
    (store / "pages_manifest.json").write_text(json.dumps(manifest), "utf-8")
    return store


def code(exc_info):
    return exc_info.value.error.code


def test_pages_are_returned_with_a_hash_and_printed_label(knowledge_copy):
    build_store(knowledge_copy)
    page = PageStore(RuleRegistry(knowledge_copy)).get_pages("book-a-2010", 2, 3)
    assert [p.text for p in page] == ["SENTINEL beta", "SENTINEL gamma"]
    assert page[0].printed_page == "2" and page[0].pdf_page == 2
    assert page[0].text_sha256 == hashlib.sha256(b"SENTINEL beta").hexdigest()


def test_printed_and_pdf_pages_differ_by_the_edition_offset(knowledge_copy):
    build_store(knowledge_copy, "book-b-2010")
    page = PageStore(RuleRegistry(knowledge_copy)).get_pages("book-b-2010", 1, 1)[0]
    assert (page.printed_page, page.pdf_page) == ("1", 2)


def test_missing_store_fails_closed(knowledge_copy):
    with pytest.raises(KnowledgeError) as exc_info:
        PageStore(RuleRegistry(knowledge_copy)).get_pages("book-a-2010", 1, 1)
    assert code(exc_info) == "DATA_UNAVAILABLE"
    assert str(knowledge_copy) not in str(exc_info.value)


def test_one_changed_byte_fails_closed(knowledge_copy):
    store = build_store(knowledge_copy)
    raw = bytearray((store / "pages.jsonl").read_bytes())
    raw[20] ^= 1
    (store / "pages.jsonl").write_bytes(bytes(raw))
    with pytest.raises(KnowledgeError) as exc_info:
        PageStore(RuleRegistry(knowledge_copy)).get_pages("book-a-2010", 1, 1)
    assert code(exc_info) == "INTEGRITY_FAILURE"


@pytest.mark.parametrize(
    ("edition", "first", "last", "expected"),
    [
        ("book-a-2010", 1, 9, "INVALID_REFERENCE"),  # more than five pages
        ("book-a-2010", 9, 9, "NOT_FOUND"),  # not in the store
        ("no-such-edition", 1, 1, "NOT_FOUND"),
        ("../x", 1, 1, "NOT_FOUND"),
    ],
)
def test_bounds_and_unknown_editions(knowledge_copy, edition, first, last, expected):
    build_store(knowledge_copy)
    with pytest.raises(KnowledgeError) as exc_info:
        PageStore(RuleRegistry(knowledge_copy)).get_pages(edition, first, last)
    assert code(exc_info) == expected


def test_search_tolerates_marks_variants_and_the_extractors_inverted_lam_alef(knowledge_copy):
    build_store(
        knowledge_copy,
        pages={
            1: "ال يسمع البوق",  # extractor output: "لا" came out as "ال"
            2: "اإلمام يقرأ",  # "الإمام" with the lam-alef pair inverted
            3: "القَلْقَلَة في الحروف",
        },
    )
    store = PageStore(RuleRegistry(knowledge_copy))
    hit = lambda q: [h[0].printed_page for h in store.search(q, ("book-a-2010",), 10)]  # noqa: E731
    assert hit("لا يسمع") == ["1"]
    assert hit("الإمام") == ["2"]
    assert hit("القلقلة") == ["3"]
    assert hit("غير موجود") == []


def test_normalization_is_lossy_only_for_search():
    assert normalize_arabic("هللا") == "الله"
    assert normalize_arabic("أَحَد") == normalize_arabic("احد")
