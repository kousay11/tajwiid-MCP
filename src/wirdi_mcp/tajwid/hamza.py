"""Detectors for the hamza family (Book A pp.25-31), read from this corpus's orthography.

The corpus already writes Qaloun's changes (an alef between two hamzas, a hamza replaced by
a letter), so structure is read from the letters and the vowel signs. What needs a word
list is in `lexicon.py`; what would need morphology is reported as not covered.
"""

from wirdi_mcp.tajwid.lexicon import skeleton
from wirdi_mcp.tajwid.text import HAMZA_FORMS, WASL_STOP, Letter, Word
from wirdi_mcp.tajwid.view import AyahView, emit, following

FATHA, DAMMA, KASRA = chr(0x064E), chr(0x064F), chr(0x0650)
DAGGER_ALEF = chr(0x0670)
SHARED = ("drop_first_hamza_qasr", "drop_second_hamza_tawassut")
TASHIL_FIRST = ("tashil_first_with_short_alef", "tashil_first_with_connected_alef")
TWO_WORD_DIFFERENT = {
    (FATHA, DAMMA): ("tashil_second_between_hamza_and_waw",),
    (FATHA, KASRA): ("tashil_second_between_hamza_and_yeh",),
    (DAMMA, FATHA): ("second_hamza_becomes_waw_with_fatha",),
    (DAMMA, KASRA): (
        "tashil_second_between_hamza_and_yeh",
        "second_hamza_becomes_waw_with_kasra",
    ),
    (KASRA, FATHA): ("second_hamza_becomes_yeh_with_fatha",),
}
VOWEL_NAME = {FATHA: "fatha", DAMMA: "damma", KASRA: "kasra"}
ARTICLE_LAM = "ل"
SEVEN_NOUNS = ("اسم", "ابن", "ابنت", "امرء", "امرءت", "اثنان", "اثنين", "اثنتين", "اثنتان")
HAMZAT_WASL_VERB_EXCEPTIONS = ("امشوا", "ابنوا", "امضوا", "اقضوا")

HAMZA_RULES = (
    "hamza_double_in_word",
    "hamza_two_words_same",
    "hamza_two_words_different",
    "hamza_nabi",
    "hamza_nabi_exception",
    "hamzat_wasl_article",
    "hamzat_wasl_noun",
    "hamzat_wasl_verb",
    "sakin_before_hamzat_wasl",
)


def is_hamza(letter: Letter | None) -> bool:
    return letter is not None and letter.char in HAMZA_FORMS


def vowel_mark(letter: Letter) -> str | None:
    for mark in (FATHA, DAMMA, KASRA):
        if mark in letter.marks:
            return mark
    return None


def detect_double_hamza_in_word(view: AyahView) -> None:
    for word in view.words:
        letters = word.letters
        for li in range(len(letters) - 1):
            first, second = letters[li], letters[li + 1]
            if not (is_hamza(first) and is_hamza(second)):
                continue
            kind = VOWEL_NAME.get(vowel_mark(second) or "", "no vowel")
            idkhal = DAGGER_ALEF in first.marks
            note = f"two hamzas in one word; second hamza has {kind}; "
            note += "an alef is written between them" if idkhal else "no alef is written between"
            emit(view, "hamza_double_in_word", word, first, note)


def detect_two_hamzas_in_two_words(view: AyahView) -> None:
    for wi, word in enumerate(view.words[:-1]):
        last = word.letters[-1]
        if not is_hamza(last):
            continue
        # a final hamza carries its own vowel; a hamza after a madd letter keeps the word's one
        vowel = vowel_mark(last)
        nxt_word = view.words[wi + 1]
        second = nxt_word.letters[0]
        if vowel is None or not is_hamza(second) or WASL_STOP in second.marks:
            continue
        second_vowel = vowel_mark(second)
        if second_vowel is None:
            continue
        if vowel == second_vowel:
            how = SHARED if vowel == FATHA else TASHIL_FIRST
            emit(
                view,
                "hamza_two_words_same",
                word,
                last,
                f"final hamza and next word's initial hamza both have {VOWEL_NAME[vowel]}",
                how,
            )
        else:
            readings = TWO_WORD_DIFFERENT.get((vowel, second_vowel))
            if readings is None:
                continue
            emit(
                view,
                "hamza_two_words_different",
                word,
                last,
                f"final hamza {VOWEL_NAME[vowel]}, next initial hamza {VOWEL_NAME[second_vowel]}",
                readings,
            )


def detect_nabi(view: AyahView) -> None:
    for word in view.words:
        sk = skeleton(word)
        if "نبيء" in sk:
            ba = next((x for x in word.letters if x.char == "ب"), None)
            if ba is not None and not ba.has_shadda:
                emit(
                    view, "hamza_nabi", word, word.letters[0], "the word of prophet read with hamza"
                )
        elif sk in ("للنبي", "النبي") and (view.surah, 50) == (view.surah, 50):
            if view.surah == 33 and any(k in (50, 53) for k in view.kufi):
                emit(
                    view,
                    "hamza_nabi_exception",
                    word,
                    word.letters[0],
                    "read without hamza when joined to the next word; with hamza if stopped on",
                )


EMPTY_CENTRE_LOW_STOP = chr(0x06EA)  # marks the wasl alef of verbs and nouns in this corpus


def _word_alef_is_wasl(word: Word) -> bool:
    first = word.letters[0]
    return first.char == "ا" and (WASL_STOP in first.marks or EMPTY_CENTRE_LOW_STOP in first.marks)


def detect_hamzat_wasl(view: AyahView) -> None:
    for word in view.words:
        letters = word.letters
        if not _word_alef_is_wasl(word) or len(letters) < 3:
            continue
        sk = skeleton(word)
        if WASL_STOP in letters[0].marks and letters[1].char == ARTICLE_LAM:
            emit(view, "hamzat_wasl_article", word, letters[0], "article: starts with fatha")
        elif any(sk == noun or sk.startswith(noun) for noun in SEVEN_NOUNS) and (
            sk not in HAMZAT_WASL_VERB_EXCEPTIONS and not sk.startswith("ابنوا")
        ):
            emit(
                view,
                "hamzat_wasl_noun",
                word,
                letters[0],
                "one of the seven nouns: starts with kasra",
            )
        else:
            third = letters[2]
            # p.31: four verbs have a damma on the third letter that is accidental, so they begin
            # with a kasra
            damma = DAMMA in third.marks and sk not in HAMZAT_WASL_VERB_EXCEPTIONS
            start = "damma" if damma else "kasra"
            emit(
                view,
                "hamzat_wasl_verb",
                word,
                letters[0],
                f"verb form (or other word): starts with {start}",
            )


def detect_sakin_before_wasl(view: AyahView) -> None:
    for wi, word in enumerate(view.words[:-1]):
        nxt = view.words[wi + 1]
        if not _word_alef_is_wasl(nxt):
            continue
        last = word.letters[-1]
        kind = None
        if skeleton(word) == "من" and word.letters[-1].char == "ن":
            kind = "min: the noon takes a fatha"
        elif (
            last.char == "م"
            and DAMMA in last.marks
            and len(word.letters) > 2
            and word.letters[-2].char in "هكت"
        ):
            kind = "plural meem: takes a damma"
        elif last.has_tanween:
            kind = "tanween noon: takes a kasra (damma before a damma start)"
        if kind is not None:
            emit(view, "sakin_before_hamzat_wasl", word, last, kind)


HAMZA_DETECTORS = {
    "hamza_double_in_word": detect_double_hamza_in_word,
    "hamza_nabi": detect_nabi,
    "hamza_nabi_exception": detect_nabi,
    "hamzat_wasl_article": detect_hamzat_wasl,
    "hamzat_wasl_noun": detect_hamzat_wasl,
    "hamzat_wasl_verb": detect_hamzat_wasl,
    "sakin_before_hamzat_wasl": detect_sakin_before_wasl,
}
_ = following  # kept for symmetry with the other family modules
