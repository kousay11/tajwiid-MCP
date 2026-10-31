"""Ya'at al-idafa read with a fatha before a hamza (Book A pp.45-50), by the corpus spelling.

The corpus writes the first-person ya with a fatha when Qaloun opens it and with the yeh
barree when Qaloun closes it. Only the fatha is distinctive (the yeh barree also ends
ordinary words), so the open ya is detected by its spelling and the closed ones are named
by the book's word lists in `lexicon.py`.
"""

from wirdi_mcp.tajwid.lexicon import skeleton
from wirdi_mcp.tajwid.text import HAMZA_FORMS, Word
from wirdi_mcp.tajwid.view import AyahView, emit, starts_with_wasl

FATHA, KASRA = chr(0x064E), chr(0x0650)
THIRD_PERSON_PRONOUN = frozenset(("هي", "وهي", "فهي", "لهي"))


def _class_of(word: Word) -> str | None:
    first = word.letters[0]
    if first.char in HAMZA_FORMS:
        return "before a hamza"
    if starts_with_wasl(word):
        article = len(word.letters) > 1 and word.letters[1].char == "ل"
        return (
            "before hamzat al-wasl with the article"
            if article
            else ("before hamzat al-wasl with no article")
        )
    return None


def detect_ya_idafa_fath(view: AyahView) -> None:
    for wi, word in enumerate(view.words[:-1]):
        last = word.letters[-1]
        if last.char != "ي" or FATHA not in last.marks or len(word.letters) < 2:
            continue
        if KASRA not in word.letters[-2].marks or skeleton(word) in THIRD_PERSON_PRONOUN:
            continue
        kind = _class_of(view.words[wi + 1])
        if kind is not None:
            emit(view, "ya_idafa_fath", word, last, f"ya of the first person with a fatha {kind}")


MAEE_NOTE = (
    "Book A p.47: the ya of معي is open unless a fatha hamza follows. The corpus spells it "
    "{spelling}{before}. This differs from the sentence; the divergence is not arbitrated"
)


def detect_maee(view: AyahView) -> None:
    """Flag the word معي with what the corpus spells, since the book's sentence disagrees."""
    for wi, word in enumerate(view.words):
        if skeleton(word) not in ("معي", "ومعي", "فمعي"):
            continue
        last = word.letters[-1]
        spelling = "open (fatha)" if FATHA in last.marks else "closed (yeh barree)"
        nxt = view.words[wi + 1].letters[0] if wi + 1 < len(view.words) else None
        fatha_hamza = nxt is not None and nxt.char in HAMZA_FORMS and FATHA in nxt.marks
        before = ", before a fatha hamza" if fatha_hamza else ", not before a fatha hamza"
        emit(view, "ya_idafa_maee", word, last, MAEE_NOTE.format(spelling=spelling, before=before))


YAAT_DETECTORS = {"ya_idafa_fath": detect_ya_idafa_fath, "ya_idafa_maee": detect_maee}
