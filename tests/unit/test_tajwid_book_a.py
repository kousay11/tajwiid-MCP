"""Book A rules (madd, hamza, tafkhim and tarqiq, taqlil) on small orthographic fixtures.

Strings use explicit marks as this corpus spells them and are modelled on Book A's own
examples; they exercise the procedure, not the Quran text. Real-corpus counts are in the
integration tests.
"""

import pytest

from wirdi_mcp.tajwid.detectors import AyahView, run_detectors
from wirdi_mcp.tajwid.text import tokenize

SUKUN, SHADDA, MADDAH = chr(0x652), chr(0x651), chr(0x653)
FATHA, DAMMA, KASRA = chr(0x64E), chr(0x64F), chr(0x650)
FATHATAN = chr(0x64B)
SMALL_WAW, DAGGER, WASL, LOW_STOP = chr(0x6E5), chr(0x670), chr(0x6EC), chr(0x6EA)


def found(text, rule, *, mode="waqf", stops=None, surah=None, ayah=None, kufi=()):
    stops_at_end = (mode == "waqf") if stops is None else stops
    view = AyahView(
        words=tokenize(text),
        mode=mode,
        stops_at_end=stops_at_end,
        surah=surah,
        ayah=ayah,
        kufi=kufi,
    )
    run_detectors(view, frozenset((rule,)))
    return [(o.rule_id, text[o.start : o.end], o.variants) for o in view.occurrences], view


def rules_in(text, rule, **kw):
    return [r for r, _, _ in found(text, rule, **kw)[0]]


# --- madd ---------------------------------------------------------------------------------
def test_natural_madd_is_a_bare_alef_after_a_fatha():
    text = "ق" + FATHA + "ا" + "ل" + FATHA + " ر" + FATHA + "ب" + DAMMA
    assert rules_in(text, "madd_tabii") == ["madd_tabii"]


def test_a_wasl_alef_before_a_sukun_is_not_a_madd_letter():
    # the alef after a conjunction prefix, before the sakin lam of the article (book A p.29)
    text = "و" + FATHA + "ا" + "ل" + SUKUN + "ح" + KASRA + "ج" + FATHA + " ر" + FATHA
    assert not [s for _, s, _ in found(text, "madd_tabii")[0] if s.startswith("ا")]


def test_madd_badal_follows_a_hamza():
    text = "ء" + FATHA + "ا" + "م" + FATHA + "ن" + FATHA + " ر" + FATHA
    assert rules_in(text, "madd_badal") == ["madd_badal"]


def test_connected_madd_has_a_hamza_in_the_same_word():
    text = "ج" + FATHA + "ا" + MADDAH + "ء" + FATHA + "ك" + DAMMA + " ر" + FATHA
    hits, _ = found(text, "madd_muttasil")
    assert [r for r, _, _ in hits] == ["madd_muttasil"]
    assert hits[0][2] == ("3_harakat", "4_harakat")


def test_separated_madd_needs_the_next_word_to_start_with_a_hamza():
    text = "م" + FATHA + "ا" + " أ" + DAMMA + "ن" + "ز" + KASRA + "ل" + FATHA
    hits, _ = found(text, "madd_munfasil")
    assert [r for r, _, _ in hits] == ["madd_munfasil"]
    assert hits[0][2] == ("2_harakat", "3_harakat", "4_harakat")


def test_separated_madd_at_the_end_of_the_selection_needs_the_following_ayah():
    text = "م" + FATHA + "ا"
    _, view = found(text, "madd_munfasil", mode="wasl", stops=False)
    assert sum(view.unresolved.values()) == 1


def test_iwad_only_at_a_stop_and_never_on_the_feminine_ta():
    text = "ك" + KASRA + "ت" + FATHA + "ا" + "ب" + FATHATAN
    assert rules_in(text, "madd_iwad") == ["madd_iwad"]
    assert rules_in(text, "madd_iwad", mode="wasl") == []
    assert rules_in("ر" + FATHA + "ح" + FATHA + "م" + FATHA + "ة" + FATHATAN, "madd_iwad") == []


def test_arid_and_lin_apply_only_before_the_last_letter_of_a_stopped_word():
    arid = "م" + KASRA + "ي" + "ن" + FATHA
    assert rules_in(arid, "madd_arid_sukun") == ["madd_arid_sukun"]
    assert rules_in(arid, "madd_arid_sukun", mode="wasl") == []
    lin = "ب" + FATHA + "ي" + SUKUN + "ت" + FATHA
    assert rules_in(lin, "madd_lin") == ["madd_lin"]


def test_lazim_kalimi_needs_a_shadda_after_a_maddah_marked_alef():
    text = "ض" + SHADDA + FATHA + "ا" + MADDAH + "ل" + SHADDA + KASRA + "ي" + "ن" + FATHA
    assert rules_in(text, "madd_lazim_kalimi_muthaqqal") == ["madd_lazim_kalimi_muthaqqal"]


@pytest.mark.parametrize(
    ("ayah_text", "muth", "mukh"),
    [
        ("أ" + FATHA + "ل" + FATHA + MADDAH + "م" + SHADDA + KASRA + MADDAH, 1, 1),  # الم
        ("ح" + FATHA + "م" + KASRA + MADDAH, 0, 1),  # حم: the ha is natural, the meem is lazim
        ("ص" + FATHA + MADDAH, 0, 1),  # ص
    ],
)
def test_fawatih_letters(ayah_text, muth, mukh):
    assert len(found(ayah_text, "madd_lazim_harfi_muthaqqal", surah=2, ayah=1)[0]) == muth
    assert len(found(ayah_text, "madd_lazim_harfi_mukhaffaf", surah=2, ayah=1)[0]) == mukh
    # the same string in a verse that is not an opening is not a letter name
    assert found(ayah_text, "madd_lazim_harfi_mukhaffaf", surah=2, ayah=2)[0] == []


def test_hay_tahar_letters_have_a_natural_madd():
    text = "ح" + FATHA + "م" + KASRA + MADDAH
    assert rules_in(text, "madd_harf_hay_tahar", surah=40, ayah=1) == ["madd_harf_hay_tahar"]


def test_sila_follows_the_corpus_mark_and_the_next_word():
    base = "ل" + FATHA + "ه" + DAMMA + SMALL_WAW
    assert rules_in(base + " ذ" + FATHA, "madd_sila_sughra_ha") == ["madd_sila_sughra_ha"]
    assert rules_in(base + " أ" + FATHA, "madd_sila_kubra_ha") == ["madd_sila_kubra_ha"]
    # at a stop the lengthening is not pronounced and is counted as skipped
    _, view = found(base, "madd_sila_sughra_ha")
    assert view.skipped


def test_plural_meem_lists_both_permitted_readings():
    text = "ل" + FATHA + "ه" + DAMMA + "م" + SUKUN + " ي" + DAMMA
    hits, _ = found(text, "madd_sila_sughra_meem")
    assert hits and hits[0][2] == ("iskan", "sila_2_harakat")
    kubra, _ = found("ل" + FATHA + "ه" + DAMMA + "م" + SUKUN + " أ" + FATHA, "madd_sila_kubra_meem")
    assert kubra and "sila_4_harakat" in kubra[0][2]


def test_a_madd_letter_is_dropped_before_the_sakin_after_hamzat_wasl():
    text = "ف" + KASRA + "ي" + " ا" + KASRA + WASL + "ل" + SUKUN + "أ" + FATHA + "ر"
    assert rules_in(text, "madd_letter_dropped") == ["madd_letter_dropped"]


# --- hamza --------------------------------------------------------------------------------
def test_two_hamzas_in_one_word_report_the_inserted_alef():
    with_alef = "أ" + FATHA + DAGGER + "ئ" + KASRA + "ن" + SHADDA + FATHA
    hits, _ = found(with_alef, "hamza_double_in_word")
    assert [r for r, _, _ in hits] == ["hamza_double_in_word"]
    plain = "أ" + FATHA + "ئ" + KASRA + "م" + SHADDA + FATHA + "ة"
    note = next(o.note for o in found(plain, "hamza_double_in_word")[1].occurrences)
    assert note and "no alef" in note


def test_the_word_aimma_is_the_book_exception():
    aimma = "أ" + FATHA + "ئ" + KASRA + "م" + SHADDA + FATHA + "ة"
    assert rules_in(aimma, "hamza_double_exception") == ["hamza_double_exception"]


def test_prophet_is_read_with_hamza_but_not_when_the_ba_has_a_shadda():
    noun = "ا" + WASL + "ل" + "ن" + SHADDA + FATHA + "ب" + KASRA + "ي" + "ء" + DAMMA
    verb = "ن" + FATHA + "ب" + SHADDA + KASRA + "ي" + "ء" + SUKUN + "ه" + DAMMA + "م" + SUKUN
    assert rules_in(noun, "hamza_nabi") == ["hamza_nabi"]
    assert rules_in(verb, "hamza_nabi") == []


def test_prophet_exception_is_limited_to_the_two_named_places():
    plain = "ا" + WASL + "ل" + "ن" + SHADDA + FATHA + "ب" + KASRA + "ي" + SHADDA + KASRA
    assert rules_in(plain, "hamza_nabi_exception", surah=33, ayah=53, kufi=(53,)) == [
        "hamza_nabi_exception"
    ]
    assert rules_in(plain, "hamza_nabi_exception", surah=33, ayah=10, kufi=(10,)) == []
    assert rules_in(plain, "hamza_nabi_exception", surah=2, ayah=53, kufi=(53,)) == []


def test_hamzat_wasl_kinds():
    article = "ا" + WASL + "ل" + SUKUN + "ح" + FATHA + "م" + SUKUN
    assert rules_in(article, "hamzat_wasl_article") == ["hamzat_wasl_article"]
    noun = "ا" + LOW_STOP + "س" + SUKUN + "م" + DAMMA + "ه" + DAMMA
    assert rules_in(noun, "hamzat_wasl_noun") == ["hamzat_wasl_noun"]
    verb = "ا" + LOW_STOP + "خ" + SUKUN + "ر" + DAMMA + "ج" + SUKUN
    hits, _ = found(verb, "hamzat_wasl_verb")
    assert hits and hits[0][0] == "hamzat_wasl_verb"


def test_sakin_before_wasl_recognises_min_and_the_plural_meem():
    wasl_word = " ا" + FATHA + WASL + "ل" + SUKUN + "ا" + "ر" + SUKUN
    assert rules_in("م" + KASRA + "ن" + FATHA + wasl_word, "sakin_before_hamzat_wasl") == [
        "sakin_before_hamzat_wasl"
    ]
    assert rules_in(
        "ل" + FATHA + "ه" + DAMMA + "م" + DAMMA + wasl_word, "sakin_before_hamzat_wasl"
    ) == ["sakin_before_hamzat_wasl"]


@pytest.mark.parametrize(
    ("rule", "text", "surah", "kufi"),
    [
        ("hamza_ibdal_yajuj", "ي" + FATHA + "ا" + "ج" + DAMMA + "و" + "ج" + FATHA, 18, (94,)),
        (
            "hamza_ibdal_minsaa",
            "م" + KASRA + "ن" + "س" + FATHA + "ا" + "ت" + FATHA + "ه" + DAMMA,
            34,
            (14,),
        ),
        ("imala_har", "ه" + "ا" + "ر" + KASRA, 9, (109,)),
        (
            "taqlil_tawrat",
            "ا"
            + WASL
            + "ل"
            + "ت"
            + SHADDA
            + FATHA
            + "و"
            + SUKUN
            + "ر"
            + FATHA
            + "ى"
            + DAGGER
            + "ة"
            + FATHA,
            3,
            (3,),
        ),
    ],
)
def test_word_lists_follow_the_place_the_book_names(rule, text, surah, kufi):
    assert rules_in(text, rule, surah=surah, ayah=kufi[0], kufi=kufi) == [rule]
    if rule in (
        "hamza_ibdal_minsaa",
        "imala_har",
    ):  # named place: the same spelling elsewhere is not it
        assert rules_in(text, rule, surah=2, ayah=1, kufi=(1,)) == []


# --- tafkhim and tarqiq -------------------------------------------------------------------
def test_ra_with_fatha_is_heavy_and_with_kasra_is_light():
    assert rules_in("ر" + FATHA + "ب" + SHADDA + FATHA, "ra_tafkhim") == ["ra_tafkhim"]
    assert rules_in("ر" + KASRA + "ز" + SUKUN + "ق" + FATHA, "ra_tarqiq") == ["ra_tarqiq"]


def test_sakin_ra_after_a_kasra_and_before_an_isti_la_letter_is_heavy():
    heavy = "ق" + KASRA + "ر" + SUKUN + "ط" + FATHA + "ا" + "س" + KASRA
    light = "ف" + KASRA + "ر" + SUKUN + "ع" + FATHA + "و" + SUKUN + "ن" + FATHA
    assert rules_in(heavy, "ra_tafkhim") == ["ra_tafkhim"]
    assert rules_in(light, "ra_tarqiq") == ["ra_tarqiq"]


def test_firq_lists_both_readings():
    hits, _ = found("ف" + KASRA + "ر" + SUKUN + "ق" + KASRA, "ra_jawaz")
    assert hits and hits[0][2] == ("tafkhim", "tarqiq")


def test_final_ra_at_a_stop_depends_on_what_precedes_it():
    assert rules_in("ا" + "ل" + "ن" + FATHA + "ا" + "ر" + KASRA, "ra_mutatarrif_tafkhim") == [
        "ra_mutatarrif_tafkhim"
    ]
    assert rules_in("خ" + FATHA + "ب" + KASRA + "ي" + "ر" + FATHA, "ra_mutatarrif_tarqiq") == [
        "ra_mutatarrif_tarqiq"
    ]
    assert (
        rules_in("ا" + "ل" + "ن" + FATHA + "ا" + "ر" + KASRA, "ra_mutatarrif_tafkhim", mode="wasl")
        == []
    )


def test_lam_of_allah_follows_the_preceding_vowel():
    name = "ا" + WASL + "ل" + "ل" + SHADDA + FATHA + "ه" + DAMMA
    after_fatha = "ق" + FATHA + "ا" + "ل" + FATHA + " " + name
    after_kasra = "ب" + KASRA + "ا" + "ل" + "ل" + SHADDA + FATHA + "ه" + KASRA
    assert rules_in(after_fatha, "lam_jalala_tafkhim") == ["lam_jalala_tafkhim"]
    assert rules_in(after_kasra, "lam_jalala_tarqiq") == ["lam_jalala_tarqiq"]


def test_madd_alef_is_heavy_after_an_isti_la_letter():
    assert rules_in("ق" + FATHA + "ا" + "ل" + FATHA, "alef_tafkhim") == ["alef_tafkhim"]
    assert rules_in("ك" + FATHA + "ا" + "ن" + FATHA, "alef_tarqiq") == ["alef_tarqiq"]


def test_ghunna_is_heavy_only_before_the_five_heavy_ikhfa_letters():
    heavy = "م" + KASRA + "ن" + " ص" + KASRA + "ي" + "ا" + "م" + KASRA
    light = "م" + KASRA + "ن" + " ك" + DAMMA + "ل" + SUKUN
    assert rules_in(heavy, "ghunna_tafkhim") == ["ghunna_tafkhim"]
    assert rules_in(light, "ghunna_tarqiq") == ["ghunna_tarqiq"]


# --- letter data (book A pp.40-45) -----------------------------------------------------------
def test_letter_tables_match_the_counts_the_book_states():
    from wirdi_mcp.tajwid import letters as t

    assert len(t.ALL_LETTERS) == 29
    assert (len(t.HAMS), len(t.SHIDDA), len(t.BAYNIYYA)) == (10, 8, 5)
    assert (len(t.ISTIALA), len(t.ITBAQ), len(t.IDHLAQ)) == (7, 4, 6)
    assert len(t.ALL_LETTERS) - len(t.HAMS) == 19  # jahr
    assert len(t.ALL_LETTERS) - len(t.SHIDDA) - len(t.BAYNIYYA) == 16  # rakhawa
    assert len(t.ALL_LETTERS) - len(t.ITBAQ) == 25  # infitah
    places = {(r, p) for r, p, _ in t._PLACES}
    assert len(places) == 17
    assert set(t.MAKHRAJ) == set(t.ALL_LETTERS) - set()  # every letter has one place


def test_letter_properties_examples_from_the_book():
    from wirdi_mcp.tajwid.letters import properties

    ba = properties("ب")
    assert ba.paired == ("jahr", "shidda", "istifal", "infitah", "idhlaq")  # book p.45
    ha = properties("ح")
    assert ha.paired == ("hams", "rakhawa", "istifal", "infitah", "ismat")  # book p.45
    assert "qalqala" in ba.other and "takrir" in properties("ر").other


# --- ya'at al-idafa, idgham, ana, fixed alefs ---------------------------------------------------
YEH_BARREE = chr(0x6D2)


def test_open_ya_before_a_hamza_is_reported_and_the_closed_one_is_not():
    open_ya = "إ" + KASRA + "ن" + SHADDA + KASRA + "ي" + FATHA + " أ" + FATHA + "ع" + SUKUN
    closed = "إ" + KASRA + "ن" + SHADDA + KASRA + YEH_BARREE + " أ" + FATHA + "ع" + SUKUN
    assert rules_in(open_ya, "ya_idafa_fath") == ["ya_idafa_fath"]
    assert rules_in(closed, "ya_idafa_fath") == []
    # the third-person pronoun is not a first-person ya
    pronoun = "ه" + KASRA + "ي" + FATHA + " أ" + FATHA + "ع" + SUKUN
    assert rules_in(pronoun, "ya_idafa_fath") == []


def test_closed_ya_exceptions_need_their_place_and_the_following_hamza():
    word = "ف" + FATHA + "ا" + "ذ" + SUKUN + "ك" + DAMMA + "ر" + DAMMA + "و" + "ن" + KASRA
    text = word + YEH_BARREE + " أ" + FATHA + "ذ" + SUKUN
    assert rules_in(text, "ya_idafa_iskan_exception", surah=2, ayah=151, kufi=(152,)) == [
        "ya_idafa_iskan_exception"
    ]
    assert rules_in(text, "ya_idafa_iskan_exception", surah=2, ayah=151, kufi=(151,)) == []
    assert (
        rules_in(word + YEH_BARREE + " ك" + FATHA, "ya_idafa_iskan_exception", surah=2, kufi=(152,))
        == []
    )


def test_general_idgham_is_read_from_the_pair_and_excludes_the_article_lam():
    mutamathilayn = "ق" + FATHA + "د" + " د" + SHADDA + FATHA + "خ" + FATHA + "ل" + FATHA
    assert rules_in(mutamathilayn, "idgham_mutamathilayn") == ["idgham_mutamathilayn"]
    mutajanisayn = "ق" + FATHA + "د" + " ت" + SHADDA + FATHA + "ب" + FATHA
    assert rules_in(mutajanisayn, "idgham_mutajanisayn") == ["idgham_mutajanisayn"]
    mutaqaribayn = "ق" + FATHA + "ل" + " ر" + SHADDA + KASRA + "ب" + SHADDA + KASRA
    assert rules_in(mutaqaribayn, "idgham_mutaqaribayn") == ["idgham_mutaqaribayn"]
    article = "ا" + WASL + "ل" + "ر" + SHADDA + FATHA + "ح" + SUKUN
    assert rules_in(article, "idgham_mutaqaribayn") == []


def test_alef_of_ana_depends_on_the_next_word():
    ana = "أ" + FATHA + "ن" + FATHA + "ا"
    assert rules_in(
        ana + " أ" + FATHA + "ن", "alef_ana_before_hamza", mode="wasl", stops=False
    ) == ["alef_ana_before_hamza"]
    hits, _ = found(
        ana + " إ" + KASRA + "ن", "alef_ana_before_hamza_kasra", mode="wasl", stops=False
    )
    assert hits and hits[0][2] == ("drop_alef", "keep_alef_with_separated_madd")
    assert rules_in(ana + " ك" + FATHA + "ل", "alef_ana_dropped", mode="wasl", stops=False) == [
        "alef_ana_dropped"
    ]
    _, view = found(ana, "alef_ana_dropped")
    assert view.skipped  # at a stop the alef is kept


def test_fixed_alefs_and_repeated_interrogatives_are_tied_to_their_places():
    fixed = "ا" + "ل" + "ر" + "س" + "و" + "ل" + "ا"
    assert rules_in(fixed, "alef_thabita", surah=33, ayah=66, kufi=(66,)) == ["alef_thabita"]
    assert rules_in(fixed, "alef_thabita", surah=33, ayah=1, kufi=(1,)) == []
    anything = "ك" + FATHA + "ل" + " م"
    assert rules_in(anything, "istifham_repeated_first", surah=13, ayah=5, kufi=(5,)) == [
        "istifham_repeated_first"
    ]
    assert rules_in(anything, "istifham_repeated_first", surah=13, ayah=6, kufi=(6,)) == []


def test_a_pronoun_ha_of_the_exception_list_is_named():
    word = "ن" + DAMMA + "ؤ" + SUKUN + "ت" + KASRA + "ه" + KASRA
    assert rules_in(word, "madd_sila_ha_exception") == ["madd_sila_ha_exception"]


# --- words Book A states in two ways ------------------------------------------------------------
TWO_WAYS = ("without_sila", "with_sila")


def test_the_two_words_book_a_states_in_two_ways_keep_both_readings():
    falqihi = "ف" + FATHA + "أ" + FATHA + "ل" + SUKUN + "ق" + KASRA + "ه" + KASRA
    yatihi = "ي" + FATHA + "أ" + SUKUN + "ت" + KASRA + "ه" + KASRA
    for word in (falqihi, yatihi):
        hits, _ = found(word, "madd_sila_ha_exception")
        assert hits and hits[0][2] == TWO_WAYS


def test_falqihi_note_names_both_pages_and_the_contradiction():
    from wirdi_mcp.tajwid.lexicon import LEXEMES

    note = next(lx.note for lx in LEXEMES if lx.pattern.pattern == "^فءلقه$")
    assert "p.19" in note and "p.20" in note and "contradicts" in note
    assert "none is chosen" in note


def test_words_without_a_double_reading_have_no_variants():
    nuteihi = "ن" + DAMMA + "ؤ" + SUKUN + "ت" + KASRA + "ه" + KASRA
    hits, _ = found(nuteihi, "madd_sila_ha_exception")
    assert hits and hits[0][2] == ()


def test_every_lexeme_note_fits_the_annotation_limit():
    from wirdi_mcp.tajwid.lexicon import LEXEMES

    assert all(len(lx.note) <= 300 for lx in LEXEMES)


def test_alan_keeps_its_three_readings_and_the_sukun_case_keeps_none():
    from wirdi_mcp.tajwid.lexicon import LEXEMES

    alan = next(lx for lx in LEXEMES if lx.pattern.pattern == "^ءالن$")
    assert alan.variants == ("madd_6_harakat", "madd_2_harakat", "tashil_without_madd")
    assert alan.places == ((10, 51), (10, 91)) and "none is chosen" in alan.note
    # the structural case (a maddah alef before an original sukun) lists no reading
    text = "م" + FATHA + "ح" + SUKUN + "ي" + FATHA + "ا" + MADDAH + "ي" + SUKUN
    hits, _ = found(text, "madd_lazim_kalimi_mukhaffaf")
    assert hits and hits[0][2] == ()
