"""Words that Book A names one by one, matched on a normalized skeleton of the corpus text.

The skeleton keeps only base letters: every hamza form becomes a bare hamza, alef madda
becomes alef, alef maqsura and the yeh barree become yeh. Marks are ignored. Where the
book gives a place it is a Kufian ayah number (the numbering of the printed copy it
teaches from), which is compared with the Kufian links of the Qaloun ayah. A listed word
that is not found is a corpus-audit finding, never something the detector invents.
"""

import re
from dataclasses import dataclass

from wirdi_mcp.tajwid.text import HAMZA_FORMS, Word
from wirdi_mcp.tajwid.view import WASL_ALEF_MARKS, AyahView, Occurrence, starts_with_wasl

ALEF_MADDA = chr(0x0622)
ALEF_MAQSURA, YEH_BARREE = chr(0x0649), chr(0x06D2)


def skeleton(word: Word) -> str:
    out = []
    for letter in word.letters:
        ch = letter.char
        if ch == ALEF_MADDA:
            ch = "ا"
        elif ch in HAMZA_FORMS:
            ch = "ء"
        elif ch in (ALEF_MAQSURA, YEH_BARREE):
            ch = "ي"
        out.append(ch)
    return "".join(out)


@dataclass(frozen=True)
class Lexeme:
    rule_id: str
    pattern: re.Pattern[str]
    note: str
    # Kufian (surah, ayah) places named by the book; None means every occurrence.
    places: tuple[tuple[int, int], ...] | None = None
    variants: tuple[str, ...] = ()
    # True when the book names a whole ayah, not a word: the first word of the ayah is the anchor.
    verse_level: bool = False
    # What the next word must begin with: "hamza" (a hamza qat') or "wasl" (hamzat al-wasl).
    next_word: str | None = None


def _lex(rule_id, pattern, note, places=None, variants=(), verse_level=False, next_word=None):
    return Lexeme(rule_id, re.compile(pattern), note, places, variants, verse_level, next_word)


LEXEMES: tuple[Lexeme, ...] = (
    # Book A p.25: single hamza replaced or changed.
    _lex(
        "hamza_ibdal_yajuj", r"^[يم]اجوج$|^و[يم]اجوج$", "hamza replaced by alef in Yajuj and Majuj"
    ),
    _lex(
        "hamza_ibdal_ruya",
        r"^وريا$",
        "hamza replaced by yeh and merged in the next yeh",
        ((19, 74),),
    ),
    _lex("hamza_ibdal_minsaa", r"^منساته$", "hamza replaced by alef", ((34, 14),)),
    _lex("hamza_ibdal_saala", r"^سال$", "hamza replaced by alef", ((70, 1),)),
    _lex("hamza_ibdal_musada", r"^موصدة$", "hamza replaced by waw", ((90, 20), (104, 8))),
    _lex("hamza_waw_huzu_kufu", r"^هزءا$|^كفءا$", "waw read as hamza on the waw (huzu, kufu)"),
    # Book A p.20-21: lazim kalimi mukhaffaf besides the one detected from its sukun.
    _lex(
        "madd_lazim_kalimi_mukhaffaf",
        r"^ءالن$",
        "madd letter before a lam in the word spelled with the interrogative hamza",
        ((10, 51), (10, 91)),
    ),
    # Book A p.26-27: the exceptions to the double-hamza-in-a-word rule.
    _lex(
        "hamza_double_exception",
        r"^ءءمة$|^ءءمه$",
        "two hamzas in one word with no alef between them: only the second is softened",
    ),
    _lex(
        "hamza_double_exception",
        r"^ءشهدوا$",
        "added interrogative hamza before a damma hamza: two readings (with or without the alef)",
        ((43, 19),),
        ("with_alef_between", "without_alef_between"),
    ),
    # Book A p.20: the pronoun ha is vowelled without the lengthening in these words.
    _lex(
        "madd_sila_ha_exception",
        r"^(?:ف|و)?(?:نءته|نوله|نصله|ءرجه|يتقه|يءته|فءلقه|يءده)$",
        "pronoun ha with a kasra and no lengthening, though its conditions are met",
    ),
    # Book A p.24: alefs that are kept when stopping and when joining.
    _lex("alef_thabita", r"^لكنا$", "alef kept when joined and when stopped", ((18, 38),)),
    _lex(
        "alef_thabita",
        r"^(?:الظنونا|الرسولا|السبيلا)$",
        "alef kept when joined and when stopped",
        ((33, 10), (33, 66), (33, 67)),
    ),
    # Book A p.26-27: added interrogative hamza and repeated interrogatives.
    _lex(
        "hamza_istifham_added",
        r"^ءامنتم$",
        "interrogative hamza added: the second hamza is softened with no alef between them",
        ((7, 123), (20, 71), (26, 49)),
    ),
    _lex(
        "hamza_istifham_added",
        r"^ءالهتنا$",
        "second hamza softened between hamza and alef",
        ((43, 58),),
    ),
    *(
        _lex(
            "istifham_repeated_first",
            r".*",
            "repeated interrogative: kept in the first clause, dropped in the second",
            ((surah, ayah),),
            verse_level=True,
        )
        for surah, ayah in (
            (13, 5),
            (17, 49),
            (17, 98),
            (23, 82),
            (32, 10),
            (37, 16),
            (37, 53),
            (56, 47),
            (79, 10),
            (79, 11),
        )
    ),
    *(
        _lex(
            "istifham_repeated_second",
            r".*",
            "repeated interrogative: dropped in the first clause, kept in the second",
            ((surah, ayah),),
            verse_level=True,
        )
        for surah, ayah in ((27, 67), (29, 28), (29, 29))
    ),
    # Book A p.38: idgham of the noon of the word below into the noon after it.
    _lex(
        "idgham_kabir_mutamathil",
        r"^تءمنا$",
        "the noon of the verb merges into the next noon with a hint of the damma",
        ((12, 11),),
    ),
    # Book A p.38-39: complete-letter assimilation that keeps the first letter's quality.
    _lex(
        "idgham_naqis",
        r"^(?:بسطت|فرطتم|ءحطت|فرطت)$",
        "the letter is assimilated but keeps its own quality (no bounce)",
    ),
    # Book A pp.48-50: first-person ya read with sukun although the rule for its class is fath.
    *(
        _lex(
            "ya_idafa_iskan_exception",
            pattern,
            note,
            places,
            next_word="wasl" if "wasl" in note else "hamza",
        )
        for pattern, note, places in (
            (r"^ف?اذكروني$", "before a hamza with a fatha", ((2, 152),)),
            (r"^ءرني$", "before a hamza with a fatha", ((7, 143),)),
            (r"^تفتني$", "before a hamza with a fatha", ((9, 49),)),
            (r"^و?ترحمني$", "before a hamza with a fatha", ((11, 47),)),
            (r"^ف?اتبعني$", "before a hamza with a fatha", ((19, 43),)),
            (r"^ءوزعني$", "before a hamza with a fatha", ((27, 19), (46, 15))),
            (r"^ذروني$", "before a hamza with a fatha", ((40, 26),)),
            (r"^ادعوني$", "before a hamza with a fatha", ((40, 60),)),
            (r"^ءنظرني$", "before a hamza with a kasra", ((7, 14),)),
            (r"^يدعونني$", "before a hamza with a kasra", ((12, 33),)),
            (r"^ءخوتي$", "before a hamza with a kasra", ((12, 100),)),
            (r"^فءنظرني$", "before a hamza with a kasra", ((15, 36), (38, 79))),
            (r"^يصدقني$", "before a hamza with a kasra", ((28, 34),)),
            (r"^و?تدعونني$", "before a hamza with a kasra", ((40, 41), (40, 43))),
            (r"^ذريتي$", "before a hamza with a kasra", ((46, 15),)),
            (r"^ءخرتني$", "before a hamza with a kasra", ((63, 10),)),
            (r"^بعهدي$", "before a hamza with a damma", ((2, 40),)),
            (r"^ء?اتوني$", "before a hamza with a damma", ((18, 96),)),
            (r"^ءني$", "before hamzat al-wasl with no article", ((7, 144),)),
            (r"^ءخي$", "before hamzat al-wasl with no article", ((20, 30), (20, 31))),
            (r"^ي?ليتني$", "before hamzat al-wasl with no article", ((25, 27),)),
        )
    ),
    # Book A p.50: first-person ya read with fatha although the rule for its class is sukun.
    *(
        _lex("ya_idafa_fath_exception", pattern, "before a letter that is not a hamza", places)
        for pattern, places in (
            (r"^بيتي$", ((2, 125), (22, 26))),
            (r"^وجهي$", ((6, 79),)),
            (r"^و?مماتي$", ((6, 162),)),
            (r"^و?مالي$", ((36, 22),)),
            (r"^و?لي$", ((109, 6),)),
        )
    ),
    _lex(
        "ya_idafa_rabbi_two_readings",
        r"^ربي$",
        "ya of ربي read with fatha or sukun; fatha is the reading put first",
        ((41, 50),),
        ("fath", "iskan"),
    ),
    # Book A p.35: taqlil and imala.
    _lex(
        "taqlil_tawrat", r"^(?:و|ب)?التورية$", "the alef of al-tawrat is read between alef and yeh"
    ),
    _lex("imala_har", r"^هار$", "the alef of har is inclined toward yeh", ((9, 109),)),
)


def _next_matches(view: AyahView, word: Word, expected: str) -> bool:
    if word.index >= len(view.words):
        # the word ends the ayah: the next ayah decides when the reading continues into it
        nxt = view.next_ayah_first
        if nxt is None or view.stops_at_end:
            return True
        if expected == "hamza":
            return nxt.char in HAMZA_FORMS
        return nxt.char == "ا" and any(m in nxt.marks for m in WASL_ALEF_MARKS)
    following_word = view.words[word.index]  # Word.index is 1-based, so this is the next word
    if expected == "hamza":
        return following_word.letters[0].char in HAMZA_FORMS
    return starts_with_wasl(following_word)


def detect_lexical(view: AyahView) -> None:
    for word in view.words:
        sk = skeleton(word)
        for lexeme in LEXEMES:
            if lexeme.verse_level and word.index != 1:
                continue
            if lexeme.next_word and not _next_matches(view, word, lexeme.next_word):
                continue
            if lexeme.pattern.match(sk) is None:
                continue
            if lexeme.places is not None and not any(
                (view.surah, k) in lexeme.places for k in view.kufi
            ):
                continue
            view.occurrences.append(
                Occurrence(
                    lexeme.rule_id, word.index, word.start, word.end, lexeme.note, lexeme.variants
                )
            )


LEXICAL_RULES = tuple(sorted({lexeme.rule_id for lexeme in LEXEMES}))
LEXICAL_DETECTORS = {rule: detect_lexical for rule in LEXICAL_RULES}
