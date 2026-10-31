"""Detectors for heavy and light letters (Book A pp.32-35): ra, the lam of Allah, alef, ghunna.

The vowel that decides each case is read from the corpus marks of the letter, or of the
nearest vowelled letter before it. At the start of a selection the preceding letter is
unknown, which is reported rather than guessed.
"""

import re

from wirdi_mcp.tajwid.lexicon import skeleton
from wirdi_mcp.tajwid.text import WASL_STOP, Letter, Word
from wirdi_mcp.tajwid.view import WASL_ALEF_MARKS, AyahView, emit, following

FATHA, DAMMA, KASRA = chr(0x064E), chr(0x064F), chr(0x0650)
ISTIALA = frozenset("خصضغطقظ")
EMPHATIC_IKHFA = frozenset("صضطظق")
ALEF = "ا"
RA_JAWAZ_WORDS = ((r"يسر", 89), (r"نذر", 54))


def _vowel(letter: Letter) -> str | None:
    for mark in (FATHA, DAMMA, KASRA):
        if mark in letter.marks:
            return mark
    return None


def _prev_vowel(word: Word, li: int) -> tuple[str | None, str]:
    """Vowel pronounced on the letter before letters[li] and a short account of how."""
    letters = word.letters
    k = li - 1
    while k >= 0:
        letter = letters[k]
        if letter.has_sukun and (letter.char not in "اوي" or letter.char == ALEF):
            k -= 1
            continue
        if letter.char == ALEF and not set(letter.marks) - {chr(0x0653)}:
            return FATHA, "madd alef"
        if letter.char == chr(0x0649) or chr(0x0670) in letter.marks:
            return FATHA, "alef maqsura or superscript alef"
        if letter.char == "و" and k > 0 and DAMMA in letters[k - 1].marks and not _vow(letter):
            return DAMMA, "madd waw"
        if letter.char in "يے" and k > 0 and KASRA in letters[k - 1].marks and not _vow(letter):
            return KASRA, "madd yeh"
        if letter.char in "وي" and letter.has_sukun:
            return (FATHA if k and FATHA in letters[k - 1].marks else None), "lin letter"
        return _vowel(letter), "vowel"
    return None, "none"


def _vow(letter: Letter) -> bool:
    return _vowel(letter) is not None or letter.has_shadda


def detect_ra(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        letters = word.letters
        for li, letter in enumerate(letters):
            if letter.char != "ر":
                continue
            at_end = li == len(letters) - 1
            final_stop = at_end and wi == len(view.words) - 1 and view.stops_at_end
            if final_stop:
                _ra_at_stop(view, word, li)
            else:
                _ra_inside(view, wi, word, li)


def _ra_inside(view: AyahView, wi: int, word: Word, li: int) -> None:
    letter = word.letters[li]
    own = _vowel(letter)
    if letter.has_tanween:
        own = None
    if own in (FATHA, DAMMA):
        emit(view, "ra_tafkhim", word, letter, "ra with fatha or damma")
    elif own == KASRA:
        emit(view, "ra_tarqiq", word, letter, "ra with kasra")
    elif letter.has_sukun:
        before = word.letters[li - 1] if li > 0 else None
        if before is None:
            # a sakin ra starts the word only after a wasl alef; the alef carries the verdict
            return
        if before.char == "ا" and (WASL_STOP in before.marks or chr(0x06EA) in before.marks):
            emit(view, "ra_tafkhim", word, letter, "sakin ra after a kasra that is not original")
            return
        vowel = _vowel(before)
        if vowel in (FATHA, DAMMA):
            emit(view, "ra_tafkhim", word, letter, "sakin ra after fatha or damma")
        elif vowel == KASRA:
            after = word.letters[li + 1] if li + 1 < len(word.letters) else None
            if skeleton(word) == "فرق":
                emit(
                    view,
                    "ra_jawaz",
                    word,
                    letter,
                    "sakin ra after kasra before qaf in the word firq",
                    ("tafkhim", "tarqiq"),
                )
            elif after is not None and after.char in ISTIALA and _vowel(after) != KASRA:
                emit(
                    view,
                    "ra_tafkhim",
                    word,
                    letter,
                    "sakin ra after an original kasra, then a non-kasra isti'la letter",
                )
            else:
                emit(view, "ra_tarqiq", word, letter, "sakin ra after an original kasra")


def _ra_at_stop(view: AyahView, word: Word, li: int) -> None:
    letter = word.letters[li]
    sk = skeleton(word)
    for stem, surah in RA_JAWAZ_WORDS:
        if view.surah == surah and (sk == stem or sk == "و" + stem):
            emit(
                view,
                "ra_mutatarrif_jawaz",
                word,
                letter,
                "final ra stopped on after a dropped yeh: both readings are allowed",
                ("tafkhim", "tarqiq"),
            )
            return
    if sk in ("القطر", "مصر"):
        emit(
            view,
            "ra_mutatarrif_jawaz",
            word,
            letter,
            "final ra after an isti'la letter with sukun, itself after a kasra",
            ("tafkhim", "tarqiq"),
        )
        return
    vowel, how = _prev_vowel(word, li)
    if vowel in (FATHA, DAMMA):
        emit(view, "ra_mutatarrif_tafkhim", word, letter, f"final ra stopped on after {how}")
    elif vowel == KASRA:
        emit(view, "ra_mutatarrif_tarqiq", word, letter, f"final ra stopped on after {how}")


def _lafz_jalala(word: Word) -> int | None:
    """Index of the lead lam in the name of Allah (the letter just before its doubled lam)."""
    letters = word.letters
    if len(letters) < 3 or letters[-1].char != "ه":
        return None
    if letters[-2].char != "ل" or letters[-3].char != "ل":
        return None
    prefix = letters[:-3]
    if all(x.char in "اوفبتك" for x in prefix) and len(prefix) <= 2:
        return len(letters) - 3
    return None


def _vowel_before_name(view: AyahView, wi: int, word: Word, lead: int) -> tuple[str | None, str]:
    """Vowel in force just before the heavy-or-light lam of the name of Allah."""
    letters = word.letters
    lead_letter = letters[lead]
    own = _vowel(lead_letter)
    if own is not None:
        return own, "preposition lam" if lead == 0 else "prefix lam"
    # bare lead lam is the article: the vowel comes from before its alef
    alef = lead - 1
    if alef < 0 or letters[alef].char != ALEF:
        return None, "unknown"
    if alef > 0:
        return _vowel(letters[alef - 1]), "prefix"
    if wi == 0:
        return None, "start"
    previous = view.words[wi - 1]
    last = previous.letters[-1]
    if last.has_tanween:
        return KASRA, "tanween takes a kasra"
    vowel = _vowel(last)
    if vowel is not None:
        return vowel, "previous word"
    return _prev_vowel(previous, len(previous.letters))


def detect_lam_jalala(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        lead = _lafz_jalala(word)
        if lead is None:
            continue
        lam = word.letters[-2]
        vowel, how = _vowel_before_name(view, wi, word, lead)
        if how == "start":
            emit(
                view,
                "lam_jalala_tafkhim",
                word,
                lam,
                "the name of Allah at the start of the reading is begun heavy",
            )
        elif vowel == KASRA:
            emit(view, "lam_jalala_tarqiq", word, lam, f"after a kasra ({how})")
        elif vowel in (FATHA, DAMMA):
            emit(view, "lam_jalala_tafkhim", word, lam, f"after fatha or damma ({how})")
        else:
            view.note_unresolved("the vowel before the name of Allah could not be read")


def detect_alef(view: AyahView) -> None:
    for word in view.words:
        letters = word.letters
        jalala = _lafz_jalala(word)  # index of the lead lam, or None
        for li, letter in enumerate(letters):
            if li == 0 or letter.char != ALEF or letter.has_sukun or WASL_STOP in letter.marks:
                continue
            if set(letter.marks) - {chr(0x0653)}:
                continue
            before = letters[li - 1]
            if FATHA not in before.marks:
                continue
            if before.char == "ر":
                continue  # Book A p.35: decided by detect_alef_after_ra
            nxt = letters[li + 1] if li + 1 < len(letters) else None
            if nxt is not None and (nxt.has_sukun or nxt.has_shadda):
                continue  # plain alef before a sakin is a wasl alef, not a madd letter
            heavy = before.char in ISTIALA or (jalala is not None and li > jalala)
            rule = "alef_tafkhim" if heavy else "alef_tarqiq"
            emit(view, rule, word, letter, "madd alef after an isti'la letter" if heavy else None)


DAGGER_ALEF, MADDAH = chr(0x0670), chr(0x0653)
ALEF_MAQSURA = chr(0x0649)
# Book A p.35: التوراة is the only word with taqlil after a ra; elsewhere the ra is not inclined.
INCLINED_WORDS = re.compile(r"^(?:و|ب)?التورية$")


def starts_with_wasl_at(letter: Letter) -> bool:
    return any(m in letter.marks for m in WASL_ALEF_MARKS)


def _madd_alef_at(letters: tuple[Letter, ...], k: int) -> bool:
    """A bare alef (or maqsura) that lengthens the fatha before it."""
    if k >= len(letters):
        return False
    letter = letters[k]
    if letter.char not in (ALEF, ALEF_MAQSURA) or letter.has_sukun or WASL_STOP in letter.marks:
        return False
    if set(letter.marks) - {MADDAH, DAGGER_ALEF}:
        return False
    after = letters[k + 1] if k + 1 < len(letters) else None
    return not (letter.char == ALEF and after is not None and (after.has_sukun or after.has_shadda))


def detect_alef_after_ra(view: AyahView) -> None:
    for word in view.words:
        if INCLINED_WORDS.match(skeleton(word)):
            continue
        letters = word.letters
        for li, letter in enumerate(letters):
            if letter.char != "ر" or not (FATHA in letter.marks or DAGGER_ALEF in letter.marks):
                continue
            if DAGGER_ALEF in letter.marks:
                emit(view, "alef_tafkhim_after_ra", word, letter, "superscript alef on a ra")
            elif _madd_alef_at(letters, li + 1):
                emit(
                    view,
                    "alef_tafkhim_after_ra",
                    word,
                    letters[li + 1],
                    "alef after a ra that is not inclined",
                )


ISTIALA_RANKS = {
    1: "isti'la letter with a fatha, followed by an alef",
    2: "isti'la letter with a fatha",
    3: "isti'la letter with a damma",
    4: "isti'la letter with a kasra",
}
SAKIN_RANK = {FATHA: 2, DAMMA: 3, KASRA: 4}
VOWEL_NAME = {FATHA: "fatha", DAMMA: "damma", KASRA: "kasra"}


def detect_istiala(view: AyahView) -> None:
    """Book A pp.32-33: the four ranks of heaviness of ص ض ط ظ غ خ ق, by vowel."""
    for word in view.words:
        letters = word.letters
        for li, letter in enumerate(letters):
            if letter.char not in ISTIALA:
                continue
            if letter.has_tanween:
                view.note_skipped("isti'la letter with tanween")
                continue
            if letter.has_sukun:
                before = letters[li - 1] if li else None
                if before is not None and before.char == ALEF and starts_with_wasl_at(before):
                    # the wasl alef has no vowel of its own when joined, and takes one by rule
                    # when beginning, so the rank depends on the reading and is not guessed
                    view.note_skipped("sakin isti'la letter right after a wasl alef")
                    continue
                vowel, how = _prev_vowel(word, li)
                if vowel is None:
                    view.note_unresolved(
                        "the vowel before a sakin isti'la letter could not be read"
                    )
                    continue
                rank = SAKIN_RANK[vowel]
                emit(
                    view,
                    f"istiala_rank_{rank}",
                    word,
                    letter,
                    f"sakin isti'la letter after a {VOWEL_NAME[vowel]} ({how})",
                )
                continue
            vowel = FATHA if DAGGER_ALEF in letter.marks else _vowel(letter)
            if vowel == FATHA:
                long = DAGGER_ALEF in letter.marks or _madd_alef_at(letters, li + 1)
                rank = 1 if long else 2
            elif vowel == DAMMA:
                rank = 3
            elif vowel == KASRA:
                rank = 4
            else:
                view.note_skipped("isti'la letter with no explicit vowel or sukun")
                continue
            emit(view, f"istiala_rank_{rank}", word, letter, ISTIALA_RANKS[rank])


def detect_ghunna_quality(view: AyahView) -> None:
    from wirdi_mcp.tajwid.detectors import detect_noon_sakina_and_tanween  # avoids an import cycle

    probe = AyahView(
        words=view.words,
        mode=view.mode,
        next_ayah_first=view.next_ayah_first,
        stops_at_end=view.stops_at_end,
    )
    detect_noon_sakina_and_tanween(probe)
    for occurrence in probe.occurrences:
        if occurrence.rule_id != "ikhfa_haqiqi":
            continue
        word = view.words[occurrence.word_index - 1]
        li = next(i for i, x in enumerate(word.letters) if x.start == occurrence.start)
        _, nxt = following(view, occurrence.word_index - 1, li)
        if nxt is None:
            continue
        rule = "ghunna_tafkhim" if nxt.char in EMPHATIC_IKHFA else "ghunna_tarqiq"
        emit(view, rule, word, word.letters[li], f"ikhfa before {nxt.char}")


TAFKHIM_DETECTORS = {
    "ra_tafkhim": detect_ra,
    "ra_tarqiq": detect_ra,
    "ra_jawaz": detect_ra,
    "ra_mutatarrif_tafkhim": detect_ra,
    "ra_mutatarrif_tarqiq": detect_ra,
    "ra_mutatarrif_jawaz": detect_ra,
    "lam_jalala_tafkhim": detect_lam_jalala,
    "lam_jalala_tarqiq": detect_lam_jalala,
    "alef_tafkhim": detect_alef,
    "alef_tarqiq": detect_alef,
    "alef_tafkhim_after_ra": detect_alef_after_ra,
    "istiala_rank_1": detect_istiala,
    "istiala_rank_2": detect_istiala,
    "istiala_rank_3": detect_istiala,
    "istiala_rank_4": detect_istiala,
    "ghunna_tafkhim": detect_ghunna_quality,
    "ghunna_tarqiq": detect_ghunna_quality,
}
