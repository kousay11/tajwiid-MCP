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


FIRST_FOURTEEN = frozenset(
    """ghunna_mushaddad idgham_bighunna idgham_bilaghunna idgham_shafawi idhar_halqi
    idhar_mutlaq idhar_shafawi ikhfa_haqiqi ikhfa_shafawi iqlab lam_qamariya lam_shamsiya
    qalqala_kubra qalqala_sughra""".split()
)
WAQF_ONLY = frozenset(
    """madd_arid_sukun madd_iwad madd_lin madd_muttasil_arid ra_mutatarrif_jawaz
    ra_mutatarrif_tafkhim ra_mutatarrif_tarqiq""".split()
)
NOON_TANWEEN_RULES = frozenset(
    "idhar_halqi idgham_bighunna idgham_bilaghunna iqlab ikhfa_haqiqi idhar_mutlaq".split()
)
CLOSED_LISTS = {
    "hamza_ibdal_yajuj": 4,
    "hamza_ibdal_ruya": 1,
    "hamza_ibdal_minsaa": 1,
    "hamza_ibdal_saala": 1,
    "hamza_ibdal_musada": 2,
    "hamza_nabi_exception": 2,
    "imala_har": 1,
    "ra_jawaz": 1,
    "madd_harf_hay_tahar": 22,
    "madd_lazim_harfi_muthaqqal": 10,
    "madd_lazim_harfi_mukhaffaf": 34,
    "madd_lazim_kalimi_mukhaffaf": 3,  # محياي and the two آلآن
    "hamza_double_exception": 5,  # four أئمة and one أشهدوا
    "hamza_double_in_word": 15,
    "alef_thabita": 4,  # لكنا and the three alefs of al-Ahzab
    "hamza_istifham_added": 4,
    "idgham_kabir_mutamathil": 1,
    "idgham_naqis": 4,  # بسطت، فرطتم، فرطت، أحطت
    "ya_idafa_iskan_exception": 24,  # 9 + 10 + 2 + 3 words named by the book
    "ya_idafa_fath_exception": 6,
    "ya_idafa_rabbi_two_readings": 1,
}


@pytest.fixture(scope="module")
def all_rules(engine):
    return engine.select_rules((), ())


@pytest.mark.parametrize("mode", ["waqf", "wasl"])
def test_every_single_ayah_selection_runs_without_exception(engine, all_rules, mode):
    context = ReadingContext(mode=mode)
    rows = engine.repository.load_edition("qalun")
    counts = Counter()
    for index in range(6214):
        result = engine.detect(rows, index, index, context, all_rules)
        counts.update(o.rule_id for _, o in result.occurrences)
        for verse, occurrence in result.occurrences:
            # every anchor resolves back to the unchanged text inside the ayah
            assert 0 <= occurrence.start < occurrence.end <= len(verse.row.text)
    # frequency audit: a rule with zero hits is a detector defect, unless it is a waqf-only
    # rule evaluated in wasl, where a single ayah never stops
    expected_absent = WAQF_ONLY if mode == "wasl" else frozenset()
    assert set(counts) == set(DETECTORS) - expected_absent, set(DETECTORS) ^ set(counts)
    assert all(n >= 100 for r, n in counts.items() if r in FIRST_FOURTEEN and r != "iqlab")
    assert 200 <= counts["iqlab"] <= 400
    # closed lists named by Book A: the count is part of the claim
    for rule_id, expected in CLOSED_LISTS.items():
        assert counts[rule_id] == expected, (rule_id, counts[rule_id], expected)
    total_letters = sum(len(r.text) for r in engine.repository.load_edition("qalun"))
    assert all(n < total_letters * 0.1 for n in counts.values())


def test_the_two_double_reading_sila_words_each_occur_once(engine, all_rules):
    rows = engine.repository.load_edition("qalun")
    rules = {"madd_sila_ha_exception": all_rules["madd_sila_ha_exception"]}
    two_ways, plain = 0, 0
    for index in range(6214):
        result = engine.detect(rows, index, index, ReadingContext(mode="waqf"), rules)
        for _, occurrence in result.occurrences:
            if occurrence.variants == ("without_sila", "with_sila"):
                two_ways += 1
            else:
                plain += 1
    assert (two_ways, plain) == (2, 10)  # يأته and فألقه once each; the other words 10 times


def test_alan_is_found_twice_with_three_readings(engine, all_rules):
    rows = engine.repository.load_edition("qalun")
    rules = {"madd_lazim_kalimi_mukhaffaf": all_rules["madd_lazim_kalimi_mukhaffaf"]}
    three = []
    for index in range(6214):
        result = engine.detect(rows, index, index, ReadingContext(mode="waqf"), rules)
        three += [o for _, o in result.occurrences if len(o.variants) == 3]
    assert len(three) == 2 and all("tashil_without_madd" in o.variants for o in three)


def test_idhar_mutlaq_hits_only_the_four_words_the_book_names(engine, all_rules):
    """Book A p.6 names four words; detector hits must all belong to those lexemes."""
    rows = engine.repository.load_edition("qalun")
    words = set()
    for index in range(6214):
        result = engine.detect(rows, index, index, ReadingContext(mode="waqf"), all_rules)
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
        result = engine.detect(rows, index, index, ReadingContext(mode="waqf"), all_rules)
        for verse, occurrence in result.occurrences:
            if occurrence.rule_id not in NOON_TANWEEN_RULES or not (
                occurrence.note or ""
            ).startswith("tanween"):
                continue
            marked = rows[verse.index].text[occurrence.start : occurrence.end]
            assert any(c in standard for c in marked) == (occurrence.rule_id == "idhar_halqi")


def _service(real_repo, engine):
    from wirdi_mcp.tajwid.service import TajwidService

    return TajwidService(real_repo, engine.registry)


def test_every_app_page_can_be_analysed_and_spanning_ayat_are_reported_not_duplicated(
    real_repo, engine
):
    service = _service(real_repo, engine)
    context = ReadingContext(mode="waqf")
    pages = real_repo.load_pages()
    owned_total, spanning_total = 0, 0
    for page in range(1, 560):
        result = service.analyze_page(page, context, (), (), 500, 0)
        owned_total += len(result.verses)
        spanning_total += len(result.continued_from_previous_page)
        # an ayah is analysed on the page where it starts, never also as "continued"
        owned = {(v.surah, v.ayah) for v in result.verses}
        assert not owned & {(v.surah, v.ayah) for v in result.continued_from_previous_page}
        assert all(v.page_start == page for v in result.verses)
        assert all(v.page_start < page <= v.page_end for v in result.continued_from_previous_page)
        for annotation in result.analysis.annotations:
            assert annotation.page_refs.app_page_start == page
    assert owned_total == 6214  # every ayah belongs to exactly one page
    assert spanning_total == sum(
        1 for start, end in pages if end > start for _ in range(end - start)
    )


def test_wasl_continues_across_a_page_internal_boundary_but_not_across_a_surah(real_repo, engine):
    service = _service(real_repo, engine)
    wasl = ReadingContext(mode="wasl")
    from wirdi_mcp.domain.models import PassageSelection

    selection = PassageSelection(start=real_repo.reference("qalun", 18, 45), end_ayah=52)
    inner = service.analyze(selection, wasl, ("idhar_halqi", "idgham_bighunna"), (), True, 500, 0)
    # the last position needs the next ayah; the earlier ones were resolved from the selection
    assert inner.coverage == "partial" and inner.total > 0
    following = real_repo.reference("qalun", 18, 53)
    resolved = ReadingContext(mode="wasl", following=following)
    full = service.analyze(
        selection, resolved, ("idhar_halqi", "idgham_bighunna"), (), True, 500, 0
    )
    assert full.total >= inner.total and sum(full.unresolved.values()) <= sum(
        inner.unresolved.values()
    )
    from wirdi_mcp.domain.exceptions import KnowledgeError

    wrong = ReadingContext(mode="wasl", following=real_repo.reference("qalun", 18, 60))
    import pytest

    with pytest.raises(KnowledgeError):
        service.analyze(selection, wrong, (), (), True, 10, 0)


def test_stop_after_word_truncates_the_last_ayah_and_treats_it_as_a_stop(real_repo, engine):
    service = _service(real_repo, engine)
    from wirdi_mcp.domain.models import PassageSelection

    selection = PassageSelection(start=real_repo.reference("qalun", 18, 45), end_ayah=45)
    everything = service.analyze(selection, ReadingContext(mode="wasl"), (), (), True, 500, 0)
    stopped = service.analyze(
        selection, ReadingContext(mode="wasl", stop_after_word=3), (), (), True, 500, 0
    )
    assert 0 < stopped.total < everything.total
    assert all(a.anchor.word_index <= 3 for a in stopped.annotations)


def test_paging_covers_every_occurrence_exactly_once(real_repo, engine):
    service = _service(real_repo, engine)
    from wirdi_mcp.domain.models import PassageSelection

    selection = PassageSelection(start=real_repo.reference("qalun", 2, 1), end_ayah=30)
    seen, offset = [], 0
    while offset is not None:
        page = service.analyze(selection, ReadingContext(mode="waqf"), (), (), True, 37, offset)
        seen += [a.annotation_id for a in page.annotations]
        offset = page.next_offset
    assert len(seen) == len(set(seen)) == page.total
