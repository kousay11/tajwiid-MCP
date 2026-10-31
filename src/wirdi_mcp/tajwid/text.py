"""Letter and word tokenizer over the exact Qaloun text, with reversible codepoint offsets.

Offsets are Python string indices (Unicode codepoints) into the unchanged ayah text, so a
`TextAnchor` can always be resolved back to `text[start:end]`. The tokenizer never
normalizes, reorders or rewrites the text.
"""

from dataclasses import dataclass

# Base letters. Everything else (vowels, signs, small letters, tatweel, bidi marks) is a
# mark attached to the preceding letter.
LETTERS = frozenset(
    chr(c) for c in (*range(0x0621, 0x063B), *range(0x0641, 0x064B), 0x0671, 0x06D2)
)

# Marks are spelled as code points on purpose: they are invisible or combining on screen.
FATHA, DAMMA, KASRA = chr(0x064E), chr(0x064F), chr(0x0650)
SUKUN, SHADDA = chr(0x0652), chr(0x0651)
SMALL_HIGH_MEEM = chr(0x06E2)  # written on a noon before ba in this corpus
WASL_STOP = chr(0x06EC)  # accompanies the silent alef of hamzat al-wasl in this corpus
MADDAH = chr(0x0653)
# Superscript alef and small waw/yeh carry a vowel, so the letter is not "bare".
VOWEL_CARRIERS = frozenset(chr(c) for c in (0x0670, 0x06E5, 0x06E6))
# Tanween as written in this corpus: standard marks, and stacked forms with a vowel.
TANWEEN_MARKS = frozenset(chr(c) for c in (0x064B, 0x064C, 0x064D, 0x065E, 0x0657, 0x0656))
SHORT_VOWELS = frozenset((FATHA, DAMMA, KASRA))
HAMZA_FORMS = frozenset(chr(c) for c in range(0x0621, 0x0627))
TATWEEL = chr(0x0640)
HAMZA_MARKS = frozenset((chr(0x0654), chr(0x0655)))  # hamza above / below
HAMZA_LETTER = chr(0x0621)


@dataclass(frozen=True)
class Letter:
    char: str  # logical letter; for a hamza written on a tatweel, text[start] is the tatweel
    marks: str
    start: int  # inclusive codepoint offset of the base glyph
    end: int  # exclusive; covers the letter and its attached marks

    @property
    def has_sukun(self) -> bool:
        return SUKUN in self.marks

    @property
    def has_shadda(self) -> bool:
        return SHADDA in self.marks

    @property
    def has_tanween(self) -> bool:
        return any(m in TANWEEN_MARKS for m in self.marks)

    @property
    def has_short_vowel(self) -> bool:
        return any(m in SHORT_VOWELS for m in self.marks)

    @property
    def is_bare(self) -> bool:
        """No vowel, tanween, shadda, sukun or small high meem on the letter."""
        return not (
            self.has_sukun
            or self.has_shadda
            or self.has_tanween
            or self.has_short_vowel
            or SMALL_HIGH_MEEM in self.marks
            or any(m in VOWEL_CARRIERS for m in self.marks)
        )


@dataclass(frozen=True)
class Word:
    index: int  # 1-based among tokens that contain at least one letter
    start: int
    end: int
    letters: tuple[Letter, ...]


def _carries_hamza(token: str, index: int) -> bool:
    """A tatweel followed by a hamza mark is how this corpus writes a standalone hamza."""
    for ch in token[index + 1 :]:
        if ch in LETTERS or ch == TATWEEL:
            return False
        if ch in HAMZA_MARKS:
            return True
    return False


def tokenize(text: str) -> tuple[Word, ...]:
    words: list[Word] = []
    position = 0
    for token in text.split(" "):
        start, end = position, position + len(token)
        position = end + 1
        letters: list[Letter] = []
        for i, ch in enumerate(token):
            offset = start + i
            if ch in LETTERS:
                letters.append(Letter(ch, "", offset, offset + 1))
            elif ch == TATWEEL and _carries_hamza(token, i):
                letters.append(Letter(HAMZA_LETTER, "", offset, offset + 1))
            elif letters:
                last = letters[-1]
                letters[-1] = Letter(last.char, last.marks + ch, last.start, offset + 1)
        if letters:
            words.append(Word(len(words) + 1, start, end, tuple(letters)))
    return tuple(words)
