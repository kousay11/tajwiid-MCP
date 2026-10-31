"""Book A pp.16, 17, 23, 27, 32-33 and 35: rules added after the first Book A pass.

The strings use the spelling of this corpus (taken from the real ayat) so the detectors read
the same marks they meet there. They exercise the procedure; they are not Quran data.
"""

import pytest

from wirdi_mcp.tajwid.detectors import DETECTORS, AyahView, run_detectors
from wirdi_mcp.tajwid.text import tokenize

FATHA, DAMMA, KASRA = chr(0x64E), chr(0x64F), chr(0x650)
SUKUN, SHADDA, DAGGER = chr(0x652), chr(0x651), chr(0x670)

ULIKUNA = "وَلَيَكُوناٗ"  # وليكونا 12:32
LANASFAAN = "لَنَسْفَعاَۢ"  # لنسفعا 96:15
UTUMINA = "اِ۟ؤْتُمِنَ"  # اؤتمن
ITINA = "اَ۪يـْٔتِنَا"  # ائتنا
ALAN = "اُ۬ءَلْٰنَ"  # آلآن, not a wasl + qat' pair
ARAYTUM = "أَرَٰ۬يْتُمْ"  # أرأيتم
ARAYTAKA = "أَرَٰ۬يْتَكَ"  # أرأيتك
AFARAYTUM = "أَفَرَٰ۬يْتُم"  # أفرأيتم


def view(text, mode="waqf", next_text=None, stops=None, surah=None, kufi=()):
    words = tokenize(text)
    next_first = tokenize(next_text)[0].letters[0] if next_text else None
    v = AyahView(
        words=words,
        mode=mode,
        next_ayah_first=next_first,
        stops_at_end=(mode == "waqf") if stops is None else stops,
        surah=surah,
        kufi=kufi,
    )
    run_detectors(v)
    return v


def rules(v):
    return [o.rule_id for o in v.occurrences]


def test_the_new_rules_are_registered():
    new = {
        "hamza_wasl_then_qat_in_word",
        "noon_tawkid_khafifa_stop",
        "madd_alif_lam_mim_imran",
        "hamza_arayta_tashil",
        "alef_tafkhim_after_ra",
        "istiala_rank_1",
        "istiala_rank_2",
        "istiala_rank_3",
        "istiala_rank_4",
    }
    assert new <= set(DETECTORS)


@pytest.mark.parametrize("word", [UTUMINA, ITINA])
def test_wasl_then_qat_in_one_word(word):
    assert "hamza_wasl_then_qat_in_word" in rules(view(word))


def test_alan_is_not_a_wasl_then_qat_word():
    assert "hamza_wasl_then_qat_in_word" not in rules(view(ALAN))


def test_tawkid_khafifa_words_only_at_their_place():
    stopped = view(ULIKUNA, surah=12, kufi=(32,))
    assert [o.note for o in stopped.occurrences if o.rule_id == "noon_tawkid_khafifa_stop"] == [
        "stopped on: the tanween-like noon is read as an alef"
    ]
    joined = view(ULIKUNA + " " + UTUMINA, mode="wasl", surah=12, kufi=(32,))
    note = next(o.note for o in joined.occurrences if o.rule_id == "noon_tawkid_khafifa_stop")
    assert note.startswith("joined")
    assert "noon_tawkid_khafifa_stop" not in rules(view(ULIKUNA, surah=12, kufi=(33,)))
    assert "noon_tawkid_khafifa_stop" in rules(view(LANASFAAN, surah=96, kufi=(15,)))
    assert "noon_tawkid_khafifa_stop" not in rules(view(LANASFAAN, surah=96, kufi=(16,)))


def test_alif_lam_mim_of_al_imran_has_two_readings_when_the_name_of_allah_follows():
    word = "\u0623\u064e\u0644\u064e\u0653\u0645\u0651\u0650\u0653\u06d6"
    allah = "\u0627\u064e\u06ec\u0644\u0644\u0651\u064e\u0647\u064f"
    for mode in ("waqf", "wasl"):
        v = view(word + " " + allah, mode=mode, surah=3, kufi=(1, 2))
        hit = [o for o in v.occurrences if o.rule_id == "madd_alif_lam_mim_imran"]
        assert len(hit) == 1 and hit[0].variants == ("ya_long", "ya_short")
    assert "madd_alif_lam_mim_imran" not in rules(view(word, surah=3, kufi=(1,)))
    assert "madd_alif_lam_mim_imran" not in rules(view(word + " " + allah, surah=2, kufi=(1,)))


def test_arayta_names_three_forms_and_not_the_neighbours():
    assert rules(view(ARAYTUM)).count("hamza_arayta_tashil") == 1
    assert "hamza_arayta_tashil" not in rules(view(ARAYTAKA))
    assert "hamza_arayta_tashil" not in rules(view(AFARAYTUM))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ص" + FATHA + "ا" + "ب" + KASRA + "ر", "istiala_rank_1"),  # fatha, then an alef
        ("ص" + FATHA + DAGGER + "ب" + KASRA + "ر", "istiala_rank_1"),  # superscript alef
        ("ط" + FATHA + "ب" + FATHA + "ع", "istiala_rank_2"),
        ("ض" + DAMMA + "ر" + KASRA + "ب" + FATHA, "istiala_rank_3"),
        ("ق" + KASRA + "س" + SUKUN + "م" + FATHA + "ة", "istiala_rank_4"),
        ("م" + FATHA + "ط" + SUKUN + "ل" + FATHA + "ع", "istiala_rank_2"),  # sakin after fatha
        ("م" + DAMMA + "ق" + SUKUN + "م" + FATHA + "ح", "istiala_rank_3"),  # sakin after damma
        ("ا" + KASRA + "ط" + SUKUN + "ع" + FATHA + "ا" + "م", "istiala_rank_4"),  # after kasra
    ],
)
def test_istiala_rank_follows_the_vowel(text, expected):
    found = [r for r in rules(view(text)) if r.startswith("istiala_rank")]
    assert expected in found
    assert (
        len({r for r in found if r != expected} & {f"istiala_rank_{n}" for n in (1, 2, 3, 4)}) <= 1
    )


def test_a_sakin_isti_la_letter_right_after_a_wasl_alef_is_skipped_not_guessed():
    text = "ا" + KASRA + chr(0x06EA) + "ض" + SUKUN + "ر" + KASRA + "ب"
    v = view(text)
    assert not [o for o in v.occurrences if o.rule_id.startswith("istiala_rank")]
    assert v.skipped == {"sakin isti'la letter right after a wasl alef": 1}


def test_each_istiala_letter_gets_exactly_one_rank():
    v = view("ص" + FATHA + "ب" + FATHA + "ر" + SUKUN + "ط" + DAMMA)
    ranks = [o for o in v.occurrences if o.rule_id.startswith("istiala_rank")]
    assert [o.rule_id for o in ranks] == ["istiala_rank_2", "istiala_rank_3"]


def test_alef_after_a_ra_is_heavy_and_never_light():
    for text in ("ت" + FATHA + "ر" + FATHA + "ا", "ت" + FATHA + "ر" + FATHA + "ى"):
        found = rules(view(text))
        assert "alef_tafkhim_after_ra" in found and "alef_tarqiq" not in found
    on_ra = "ت" + FATHA + "ر" + FATHA + DAGGER
    assert "alef_tafkhim_after_ra" in rules(view(on_ra))


def test_alef_after_ra_in_the_taqlil_word_is_left_to_the_taqlil_rule():
    tawrat = (
        "ا" + "ل" + "ت" + SHADDA + FATHA + "و" + SUKUN + "ر" + FATHA + "ى" + DAGGER + "ة" + FATHA
    )
    found = rules(view(tawrat))
    assert "alef_tafkhim_after_ra" not in found and "taqlil_tawrat" in found
