"""Detector behaviour on small orthographic fixtures modelled on the books' examples.

The strings are written with explicit marks as this corpus spells them; they exercise the
procedure, not the Quran text. Book pages are named where an example comes from a book.
"""

import pytest

from wirdi_mcp.tajwid.detectors import DETECTORS, AyahView, run_detectors
from wirdi_mcp.tajwid.text import tokenize

SUKUN, SHADDA = chr(0x652), chr(0x651)
FATHA, DAMMA, KASRA = chr(0x64E), chr(0x64F), chr(0x650)
DAMMATAN, KASRATAN = chr(0x64C), chr(0x64D)
STACKED = chr(0x657)  # tanween written with a stacked mark before a non-throat letter
SMALL_MEEM, WASL = chr(0x6E2), chr(0x6EC)
TATWEEL, HAMZA_ABOVE = chr(0x640), chr(0x654)


def run(text, mode="waqf", next_text=None, stops=None, rules=None):
    words = tokenize(text)
    next_first = None
    if next_text is not None:
        next_first = tokenize(next_text)[0].letters[0]
    stops_at_end = (mode == "waqf") if stops is None else stops
    view = AyahView(words=words, mode=mode, next_ayah_first=next_first, stops_at_end=stops_at_end)
    run_detectors(view, rules)
    return view, [(o.rule_id, text[o.start : o.end]) for o in view.occurrences]


def rules_of(text, **kw):
    return [r for r, _ in run(text, **kw)[1]]


def test_every_detector_has_a_rule_record_key():
    assert all(len(v) == 4 and v[1] == "1" and v[2] == "qaloun" for v in DETECTORS.values())
    assert len(DETECTORS) == 14


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        # book A p.4-5: "من هاد" noon sakina before a throat letter, two words
        ("م" + KASRA + "ن" + SUKUN + " ه" + FATHA + "ا" + "د" + KASRATAN, "idhar_halqi"),
        # tanween before a throat letter keeps the standard mark in this corpus
        (
            "ع" + FATHA + "ل" + KASRA + "ي" + "م" + DAMMATAN + " ح" + FATHA + "ك" + KASRA + "يم",
            "idhar_halqi",
        ),
        # book A p.7: noon sakina before ba
        ("م" + KASRA + "ن" + SMALL_MEEM + " ب" + FATHA + "ع" + SUKUN + "د", "iqlab"),
        # book A p.7-8: "من صيام" two words, bare noon
        ("م" + KASRA + "ن" + " ص" + KASRA + "ي" + "ا" + "م", "ikhfa_haqiqi"),
        # tanween before lam: idgham without ghunna
        ("غ" + FATHA + "ف" + "و" + "ر" + STACKED + " ل" + FATHA + "ه" + "م", "idgham_bilaghunna"),
        # book A p.5: "من رب" idgham without ghunna
        ("م" + KASRA + "ن" + " ر" + SHADDA + FATHA + "ب", "idgham_bilaghunna"),
        # book A p.6: "من يقول" idgham with ghunna
        ("م" + FATHA + "ن" + SUKUN + " ي" + FATHA + "ق" + "و" + "ل", "idgham_bighunna"),
        # book A p.6: the noon stays clear when the idgham letter is in the same word
        ("د" + DAMMA + "ن" + SUKUN + "ي" + FATHA + "ا", "idhar_mutlaq"),
        # book A p.9: mim sakina before ba / mim / another letter
        ("ت" + FATHA + "ر" + "م" + SUKUN + " ب" + "ح", "ikhfa_shafawi"),
        ("ل" + FATHA + "ه" + "م" + SUKUN + " م" + FATHA + "غ", "idgham_shafawi"),
        # the corpus writes the sakin mim before ba and mim without a sukun
        ("ه" + DAMMA + "م" + " ب" + KASRA + "ح", "ikhfa_shafawi"),
        (
            "ق"
            + DAMMA
            + "ل"
            + DAMMA
            + "و"
            + "ب"
            + KASRA
            + "ه"
            + KASRA
            + "م"
            + " م"
            + SHADDA
            + FATHA,
            "idgham_shafawi",
        ),
        ("أ" + FATHA + "ن" + "ف" + "م" + SUKUN + " ف" + KASRA + "ي", "idhar_shafawi"),
        # book A p.11 / book B p.63: noon and mim with shadda
        ("إ" + KASRA + "ن" + SHADDA + FATHA, "ghunna_mushaddad"),
        ("ث" + DAMMA + "م" + SHADDA + FATHA, "ghunna_mushaddad"),
    ],
)
def test_positive_examples(text, rule):
    assert rule in rules_of(text)


def test_tatweel_carried_hamza_is_a_throat_letter_not_the_next_waw():
    text = "ي" + FATHA + "ن" + SUKUN + TATWEEL + FATHA + HAMZA_ABOVE + "و" + SUKUN + "ن"
    assert "idhar_halqi" in rules_of(text)
    assert "idhar_mutlaq" not in rules_of(text)


@pytest.mark.parametrize(
    ("text", "mode", "expected"),
    [
        # book B p.53: qalqala sughra mid-word, kubra at the end of a word
        ("ي" + FATHA + "د" + SUKUN + "خ" + DAMMA + "ل", "waqf", ["qalqala_sughra"]),
        (
            "ل" + FATHA + "م" + SUKUN + " ي" + FATHA + "ل" + KASRA + "د" + SUKUN,
            "waqf",
            ["qalqala_kubra"],
        ),
        # final qalqala letter at a stop, with and without shadda (book B p.53)
        ("أ" + FATHA + "ح" + FATHA + "د" + DAMMATAN, "waqf", ["qalqala_kubra"]),
        ("ب" + KASRA + "ا" + "ل" + "ح" + FATHA + "ق" + SHADDA + KASRA, "waqf", ["qalqala_kubra"]),
        # the same final letters keep their vowel in a continued reading: no qalqala
        ("أ" + FATHA + "ح" + FATHA + "د" + DAMMATAN, "wasl", []),
    ],
)
def test_qalqala(text, mode, expected):
    found = [r for r in rules_of(text, mode=mode) if r.startswith("qalqala")]
    assert found == expected


def test_qalqala_degree_is_reported_in_the_note():
    view, _ = run("ب" + KASRA + "ا" + "ل" + "ح" + FATHA + "ق" + SHADDA + KASRA)
    assert [o.note for o in view.occurrences if o.rule_id == "qalqala_kubra"] == [
        "final letter at a stop, with shadda"
    ]


def article(letter_marks):
    return "ا" + FATHA + WASL + "ل" + letter_marks


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        # book A p.12-13: the article before a sun or moon letter
        (article("") + "ش" + SHADDA + FATHA + "م" + SUKUN + "س", "lam_shamsiya"),
        (article(SUKUN) + "ق" + FATHA + "م" + FATHA + "ر", "lam_qamariya"),
        ("و" + FATHA + "ا" + "ل" + "ش" + SHADDA + FATHA + "م" + SUKUN + "س", "lam_shamsiya"),
        # Qaloun spelling of "the night": the doubled lam is not written (book A p.12)
        (article("") + "ي" + SUKUN + "ل", "lam_shamsiya"),
    ],
)
def test_lam_positive(text, rule):
    assert [r for r in rules_of(text) if r.startswith("lam_")] == [rule]


@pytest.mark.parametrize(
    "text",
    [
        article(SUKUN) + "ت" + FATHA + "ق" + FATHA + "ى",  # a verb: sukun before a sun letter
        article("") + "ل" + SHADDA + FATHA + "ه",  # lafz al-jalala: separate rule family
        "ف" + FATHA + "ا" + "ل" + KASRA + "ق" + DAMMA,  # not an article
    ],
)
def test_lam_negative_and_exclusions(text):
    assert not [r for r in rules_of(text) if r.startswith("lam_")]


def test_lafz_al_jalala_exclusion_is_counted_not_hidden():
    view, _ = run(article("") + "ل" + SHADDA + FATHA + "ه")
    assert view.skipped == {"lafz al-jalala is a separate rule family": 1}


def test_tanween_at_a_stop_is_dropped_and_counted():
    view, found = run("أ" + FATHA + "ح" + FATHA + "د" + DAMMATAN)
    assert not [r for r, _ in found if r.startswith("id")]
    assert "tanween at a stop is dropped; no rule applies" in view.skipped


def test_wasl_at_the_end_of_the_selection_needs_the_following_ayah():
    text = "ع" + FATHA + "ل" + KASRA + "ي" + "م" + DAMMATAN
    view, found = run(text, mode="wasl", stops=False)
    assert found == [] and sum(view.unresolved.values()) == 1
    view, found = run(text, mode="wasl", stops=False, next_text="ح" + FATHA + "ك" + KASRA + "يم")
    assert [r for r, _ in found] == ["idhar_halqi"] and view.unresolved == {}


def test_hamzat_wasl_next_word_is_skipped_not_misclassified():
    text = "م" + KASRA + "ن" + " ا" + KASRA + WASL + "ل" + SUKUN + "ج" + KASRA + "ن"
    view, found = run(text)
    assert not [r for r, _ in found if r.startswith(("id", "ik", "iq"))]
    assert any("hamzat al-wasl" in k for k in view.skipped)


def test_letter_name_noon_with_maddah_is_out_of_scope():
    text = "ن" + chr(0x653) + " و" + FATHA + "ا" + "ل" + "ق"
    view, found = run(text)
    assert not [r for r, _ in found if r.startswith("id")]
    assert any("letter-name" in k for k in view.skipped)


def test_rule_filter_returns_only_requested_rules():
    text = "م" + KASRA + "ن" + SUKUN + " ه" + FATHA + "ا" + "د" + KASRATAN
    _view, found = run(text, rules=frozenset({"iqlab"}))
    assert found == []


def test_occurrences_resolve_back_to_the_unchanged_text():
    text = "م" + KASRA + "ن" + SUKUN + " ه" + FATHA + "ا" + "د" + KASRATAN
    view, found = run(text)
    assert text[view.occurrences[0].start : view.occurrences[0].end] == "ن" + SUKUN
