"""Shared detector plumbing: the occurrence record, the per-ayah view and neighbour lookup."""

from dataclasses import dataclass, field

from wirdi_mcp.tajwid.text import Letter, Word


@dataclass(frozen=True)
class Occurrence:
    rule_id: str
    word_index: int
    start: int
    end: int
    note: str | None = None
    # Readings the cited source permits for this occurrence; never reduced to one choice.
    variants: tuple[str, ...] = ()


@dataclass
class AyahView:
    """One ayah plus the reading context a detector may rely on."""

    words: tuple[Word, ...]
    mode: str  # "wasl" or "waqf"
    # First letter of the next ayah when the reading continues into it and it is known.
    next_ayah_first: Letter | None = None
    # True when the final word is a stop (verse end in waqf, or an explicit stop word).
    stops_at_end: bool = True
    # Position of the ayah in the Qaloun numbering, for rules tied to named places.
    surah: int | None = None
    ayah: int | None = None
    # Numbers of the same ayah in the Kufian count; Book A names places in that numbering.
    kufi: tuple[int, ...] = ()
    occurrences: list[Occurrence] = field(default_factory=list)
    unresolved: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, int] = field(default_factory=dict)

    def note_unresolved(self, reason: str) -> None:
        self.unresolved[reason] = self.unresolved.get(reason, 0) + 1

    def note_skipped(self, reason: str) -> None:
        self.skipped[reason] = self.skipped.get(reason, 0) + 1


def following(view: AyahView, wi: int, li: int) -> tuple[str, Letter | None]:
    """Next pronounced-position letter after letters[li] of words[wi], with its relation."""
    word = view.words[wi]
    if li + 1 < len(word.letters):
        return "same_word", word.letters[li + 1]
    if wi + 1 < len(view.words):
        return "next_word", view.words[wi + 1].letters[0]
    if view.stops_at_end:
        return "stop", None
    if view.next_ayah_first is not None:
        return "next_ayah", view.next_ayah_first
    return "unknown", None


def is_wasl_alef(letter: Letter | None) -> bool:
    return letter is not None and letter.char == "ا"


def emit(
    view: AyahView,
    rule_id: str,
    word: Word,
    letter: Letter,
    note: str | None,
    variants: tuple[str, ...] = (),
) -> None:
    view.occurrences.append(
        Occurrence(rule_id, word.index, letter.start, letter.end, note, variants)
    )


# Marks this corpus puts on the alef of hamzat al-wasl: the stop sign (article and a few others),
# the empty centre low stop (verbs and nouns) and the small rounded zero.
WASL_ALEF_MARKS = (chr(0x06EC), chr(0x06EA), chr(0x06DF))


def starts_with_wasl(word: Word) -> bool:
    first = word.letters[0]
    return first.char == "ا" and any(m in first.marks for m in WASL_ALEF_MARKS)
