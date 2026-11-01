"""Detectors driven by the farsh tables of the longer book (Nabhan pp.111-198).

The Qaloun text keeps only the result of two hamzas meeting in two words or of a vowel given to a
sakin letter before hamzat al-wasl, so these cases cannot be found from the letters. The book lists
the places where they happen; `farsh_places.py` holds those places as skeletons of the two words,
checked against the corpus when it was generated. A place the corpus cannot show is not listed.
"""

from collections import defaultdict

from wirdi_mcp.tajwid.farsh_places import PLACES
from wirdi_mcp.tajwid.lexicon import skeleton
from wirdi_mcp.tajwid.view import AyahView, emit

_BY_FIRST: dict[str, list[tuple]] = defaultdict(list)
for _entry in PLACES:
    _BY_FIRST[_entry[3]].append(_entry)

NOTES = {
    "hamza_two_words_same": (
        "two hamzas with the same vowel in two words (farsh table of Nabhan): the first is dropped "
        "or softened; the readings are in `variants`"
    ),
    "hamza_two_words_different": (
        "two hamzas with different vowels in two words (farsh table of Nabhan): the second is "
        "softened or replaced; the readings are in `variants`"
    ),
}


def detect_farsh_places(view: AyahView) -> None:
    for wi, word in enumerate(view.words[:-1]):
        entries = _BY_FIRST.get(skeleton(word))
        if not entries:
            continue
        following = skeleton(view.words[wi + 1])
        for rule, surah, ayah, _first, second, tag, variants in entries:
            if view.surah != surah or ayah not in view.kufi or second != following:
                continue
            note = (
                NOTES[rule]
                if rule in NOTES
                else f"sakin letter before hamzat al-wasl takes a {tag} (farsh table of Nabhan)"
            )
            emit(view, rule, word, word.letters[-1], note, variants)


FARSH_RULES = (
    "hamza_two_words_same",
    "hamza_two_words_different",
    "sakin_before_hamzat_wasl",
)
FARSH_DETECTORS = {rule: detect_farsh_places for rule in FARSH_RULES}
