"""General idgham between a sakin letter and the next one (Book A pp.36-39), by letter pairs.

The corpus writes an assimilated first letter with no sign and doubles the second letter
with a shadda, so the pair is read directly from the letters. The article lam and the noon
and meem rules are handled elsewhere and are excluded here.
"""

from wirdi_mcp.tajwid.lexicon import skeleton
from wirdi_mcp.tajwid.text import WASL_STOP, Letter, Word
from wirdi_mcp.tajwid.view import AyahView, emit

ALEF = "ا"
MUTAJANISAYN = frozenset(
    (("ت", "ط"), ("ط", "ت"), ("ت", "د"), ("د", "ت"), ("ث", "ذ"), ("ذ", "ظ"), ("ب", "م"))
)
MUTAQARIBAYN = frozenset((("ل", "ر"), ("ق", "ك"), ("ذ", "ت")))
# Words the books give two readings: idgham, or the letters kept apart (Book A pp.37-39,
# Nabhan pp.73-75). Places are Kufian (surah, ayah); the word is matched on its letters.
TWO_READINGS = {
    "يلهث": ((7, 176), ("idgham", "izhar")),
    "اركب": ((11, 42), ("idgham", "izhar")),
    "نخلقكم": ((77, 20), ("idgham_naqis", "idgham_kamil")),
}
# A waqf sign written on the first letter does not make it vowelled: the pair is read when joined.
WAQF_SIGNS = frozenset(chr(c) for c in range(0x06D6, 0x06DD))
EXCLUDED_FIRST = frozenset("اويىنةه") | frozenset("ءأؤإئ")


def _is_article_lam(word: Word, li: int) -> bool:
    letters = word.letters
    return li >= 1 and letters[li].char == "ل" and letters[li - 1].char == ALEF and li <= 2


def detect_general_idgham(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        letters = word.letters
        for li, first in enumerate(letters):
            second = _next_letter(view, wi, word, li)
            if second is None or not second.has_shadda:
                continue
            if any(m not in WAQF_SIGNS for m in first.marks) or first.char in EXCLUDED_FIRST:
                continue
            if first.char == "م" and second.char == "م":
                continue  # the mim rules cover it
            if _is_article_lam(word, li) or WASL_STOP in first.marks:
                continue
            pair = (first.char, second.char)
            variants = _two_readings(view, word)
            if pair[0] == pair[1]:
                emit(view, "idgham_mutamathilayn", word, first, "two identical letters")
            elif pair in MUTAJANISAYN:
                emit(
                    view,
                    "idgham_mutajanisayn",
                    word,
                    first,
                    f"{pair[0]} into {pair[1]}",
                    variants,
                )
            elif pair in MUTAQARIBAYN:
                emit(
                    view,
                    "idgham_mutaqaribayn",
                    word,
                    first,
                    f"{pair[0]} into {pair[1]}",
                    variants,
                )
            else:
                view.note_skipped("assimilated pair outside the book's three lists")


def _two_readings(view: AyahView, word: Word) -> tuple[str, ...]:
    place_and_variants = TWO_READINGS.get(skeleton(word))
    if place_and_variants is None:
        return ()
    place, variants = place_and_variants
    return variants if any((view.surah, k) == place for k in view.kufi) else ()


def _next_letter(view: AyahView, wi: int, word: Word, li: int) -> Letter | None:
    if li + 1 < len(word.letters):
        return word.letters[li + 1]
    if li == len(word.letters) - 1 and wi + 1 < len(view.words):
        return view.words[wi + 1].letters[0]
    return None


IDGHAM_DETECTORS = {
    "idgham_mutamathilayn": detect_general_idgham,
    "idgham_mutajanisayn": detect_general_idgham,
    "idgham_mutaqaribayn": detect_general_idgham,
}
