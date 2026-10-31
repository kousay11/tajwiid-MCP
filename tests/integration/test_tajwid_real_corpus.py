"""Detectors over the real, checksum-verified Qaloun corpus (opt-in, read-only)."""

import functools
from collections import Counter

import pytest
from conftest import REPO_KNOWLEDGE

from wirdi_mcp.domain.models import ReadingContext
from wirdi_mcp.knowledge.pages import normalize_arabic
from wirdi_mcp.knowledge.registry import RuleRegistry
from wirdi_mcp.tajwid.detectors import DETECTORS
from wirdi_mcp.tajwid.engine import TajwidEngine


@pytest.fixture(scope="module")
def engine(real_repo):
    original = real_repo.load_edition
    real_repo.load_edition = functools.cache(original)  # hash-verified once for this module
    yield TajwidEngine(real_repo, RuleRegistry(REPO_KNOWLEDGE))
    real_repo.load_edition = original


@pytest.fixture(scope="module")
def all_rules(engine):
    return engine.select_rules((), ())


@pytest.mark.parametrize("mode", ["waqf", "wasl"])
def test_every_single_ayah_selection_runs_without_exception(engine, all_rules, mode):
    context = ReadingContext(mode=mode)
    counts = Counter()
    for index in range(6214):
        result = engine.detect(index, index, context, all_rules)
        counts.update(o.rule_id for _, o in result.occurrences)
        for verse, occurrence in result.occurrences:
            # every anchor resolves back to the unchanged text inside the ayah
            assert 0 <= occurrence.start < occurrence.end <= len(verse.row.text)
    # frequency audit: a rule with zero hits is a detector defect, not an absence of rule
    assert set(counts) == set(DETECTORS), set(DETECTORS) - set(counts)
    assert all(n >= 100 for r, n in counts.items() if r != "iqlab")
    assert 200 <= counts["iqlab"] <= 400
    total_letters = sum(len(r.text) for r in engine.repository.load_edition("qalun"))
    assert all(n < total_letters * 0.1 for n in counts.values())


def test_idhar_mutlaq_hits_only_the_four_words_the_book_names(engine, all_rules):
    """Book A p.6 names four words; detector hits must all belong to those lexemes."""
    rows = engine.repository.load_edition("qalun")
    words = set()
    for index in range(6214):
        result = engine.detect(index, index, ReadingContext(mode="waqf"), all_rules)
        for verse, occurrence in result.occurrences:
            if occurrence.rule_id == "idhar_mutlaq":
                text = rows[verse.index].text
                begin = text.rfind(" ", 0, occurrence.start) + 1
                end = text.find(" ", occurrence.start)
                words.add(normalize_arabic(text[begin : end if end > 0 else None]))
    stems = ("دني", "بني", "صنو", "قنو")
    assert words and all(any(s in w for s in stems) for w in words), words


def test_corpus_orthography_agrees_with_tanween_classification(engine, all_rules):
    """Standard tanween marks appear exactly where the detector says idhar halqi."""
    standard = {chr(0x64B), chr(0x64C), chr(0x64D)}
    rows = engine.repository.load_edition("qalun")
    for index in range(0, 6214, 7):
        result = engine.detect(index, index, ReadingContext(mode="waqf"), all_rules)
        for verse, occurrence in result.occurrences:
            if not (occurrence.note or "").startswith("tanween"):
                continue
            marked = rows[verse.index].text[occurrence.start : occurrence.end]
            assert any(c in standard for c in marked) == (occurrence.rule_id == "idhar_halqi")
