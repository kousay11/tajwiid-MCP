"""Detectors for the madd family (Book A pp.14-24), read from this corpus's orthography.

The corpus writes a madd letter as a bare alef after a fatha, a bare waw after a damma or
a bare yeh after a kasra, or as a superscript alef on the preceding letter. A maddah sign
accompanies the longer kinds. Silent letters carry a sukun, which is how they are told
apart from a real madd letter. Every candidate lists the readings the source permits and
the detector never chooses between them.
"""

from dataclasses import dataclass

from wirdi_mcp.tajwid.lexicon import skeleton
from wirdi_mcp.tajwid.text import HAMZA_FORMS, MADDAH, WASL_STOP, Letter, Word
from wirdi_mcp.tajwid.view import AyahView, emit, following

FATHA, DAMMA, KASRA = chr(0x064E), chr(0x064F), chr(0x0650)
DAGGER_ALEF = chr(0x0670)
TANWEEN_FATH = frozenset((chr(0x064B), chr(0x0657)))
SILA_MARKS = frozenset((chr(0x06E5), chr(0x06E6)))
MEEM_SMALL_MARKS = frozenset((chr(0x06E2),))
ALEF, WAW, MEEM = "ا", "و", "م"
YEH_FORMS = frozenset("يے")
# Surahs whose first ayah opens with the isolated letters, in the Qaloun numbering.
FAWATIH_SURAHS = frozenset(
    (2, 3, 7, 10, 11, 12, 13, 14, 15, 19, 20, 26, 27, 28, 29, 30, 31, 32)
    + (36, 38, 40, 41, 42, 43, 44, 45, 46, 50, 68)
)
FAWATIH_LETTERS = frozenset("أالمصركهيعطسحقن")
HAY_TAHAR = frozenset("حيطهر")  # letters pronounced with a natural madd (2 harakat)
LAZIM_LETTERS = frozenset("نقصعسلكم")
AIN_LENGTHS = ("4_harakat", "6_harakat")

PLUS_LENGTHS_ARID = ("2_harakat", "4_harakat", "6_harakat")
PLUS_LENGTHS_MUNFASIL = ("2_harakat", "3_harakat", "4_harakat")
PLUS_LENGTHS_MUTTASIL_ARID = ("3_harakat", "4_harakat", "6_harakat")
PLUS_LENGTHS_MUTTASIL = ("3_harakat", "4_harakat")
SILA_MEEM_SUGHRA = ("iskan", "sila_2_harakat")
SILA_MEEM_KUBRA = ("iskan", "sila_2_harakat", "sila_3_harakat", "sila_4_harakat")

MADD_RULES = (
    "madd_tabii",
    "madd_badal",
    "madd_iwad",
    "madd_harf_hay_tahar",
    "madd_sila_sughra_ha",
    "madd_sila_sughra_meem",
    "madd_muttasil",
    "madd_munfasil",
    "madd_sila_kubra_ha",
    "madd_sila_kubra_meem",
    "madd_arid_sukun",
    "madd_muttasil_arid",
    "madd_lin",
    "madd_lazim_kalimi_muthaqqal",
    "madd_lazim_kalimi_mukhaffaf",
    "madd_lazim_harfi_muthaqqal",
    "madd_lazim_harfi_mukhaffaf",
    "madd_letter_dropped",
)


@dataclass(frozen=True)
class MaddLetter:
    li: int  # index of the letter that carries the madd (the superscript alef's carrier)
    kind: str  # "alef" | "waw" | "yeh" | "dagger" | "implicit"


def _only_maddah(letter: Letter) -> bool:
    return all(m == MADDAH for m in letter.marks)


def is_hamza(letter: Letter | None) -> bool:
    return letter is not None and letter.char in HAMZA_FORMS


def is_silent_alef(letter: Letter) -> bool:
    return letter.char == ALEF and letter.has_sukun


def _looks_like_wasl_alef(letters: tuple[Letter, ...], li: int) -> bool:
    """A plain alef before a sukun, a shadda or an assimilated article lam is hamzat al-wasl.

    Examples are the alef after a prefix in the article, or at the start of a verb after a
    conjunction. A true madd alef is never followed by such a cluster unless a maddah marks it.
    """
    if li + 1 >= len(letters):
        return False
    nxt = letters[li + 1]
    return nxt.has_sukun or nxt.has_shadda or (nxt.char == "ل" and nxt.is_bare)


def madd_letters(word: Word) -> list[MaddLetter]:
    found: list[MaddLetter] = []
    letters = word.letters
    for li, letter in enumerate(letters):
        if DAGGER_ALEF in letter.marks:
            found.append(MaddLetter(li, "dagger"))
            continue
        if letter.char in HAMZA_FORMS and MADDAH in letter.marks and not letter.has_sukun:
            # hamza written with a maddah and no alef of its own: the alef is implied
            nxt = letters[li + 1] if li + 1 < len(letters) else None
            if not (nxt is not None and nxt.char == ALEF and not nxt.has_sukun):
                found.append(MaddLetter(li, "implicit"))
            continue
        if li == 0 or WASL_STOP in letter.marks or not _only_maddah(letter):
            continue
        prev = letters[li - 1].marks
        if letter.char == ALEF and FATHA in prev:
            if MADDAH not in letter.marks and _looks_like_wasl_alef(letters, li):
                continue
            found.append(MaddLetter(li, "alef"))
        elif letter.char == WAW and DAMMA in prev:
            found.append(MaddLetter(li, "waw"))
        elif letter.char in YEH_FORMS and KASRA in prev:
            found.append(MaddLetter(li, "yeh"))
    return found


def _tail_after(word: Word, li: int) -> int:
    """Index of the first letter after the madd letter, skipping one silent alef at the end."""
    k = li + 1
    letters = word.letters
    if k < len(letters) and is_silent_alef(letters[k]) and k == len(letters) - 1:
        return len(letters)  # word-final madd letter followed only by a silent alef
    return k


def _stops_here(view: AyahView, wi: int) -> bool:
    return wi == len(view.words) - 1 and view.stops_at_end


def detect_madd(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        letters = word.letters
        spelled_with_lexical_madd = skeleton(word) == "ءالن"  # classified by the lexicon
        for ml in madd_letters(word):
            if spelled_with_lexical_madd and MADDAH in letters[ml.li].marks:
                continue
            carrier = letters[ml.li]
            k = _tail_after(word, ml.li)
            preceded_by_hamza = ml.li > 0 and is_hamza(letters[ml.li - 1])
            if ml.kind == "implicit":
                emit(view, "madd_badal", word, carrier, "hamza carrying a maddah (alef implied)")
                continue
            if k < len(letters):
                _inside_word(view, wi, word, ml, k, preceded_by_hamza)
            else:
                _word_final(view, wi, word, ml, preceded_by_hamza)


def _inside_word(
    view: AyahView, wi: int, word: Word, ml: MaddLetter, k: int, preceded_by_hamza: bool
) -> None:
    letters = word.letters
    carrier, nxt = letters[ml.li], letters[k]
    last_letter = k == len(letters) - 1
    stops = _stops_here(view, wi)
    if is_hamza(nxt):
        if last_letter and stops:
            emit(
                view,
                "madd_muttasil_arid",
                word,
                carrier,
                "madd letter before a hamza that is the last letter of a stopped word",
                PLUS_LENGTHS_MUTTASIL_ARID,
            )
        else:
            emit(
                view,
                "madd_muttasil",
                word,
                carrier,
                "madd letter and hamza in the same word",
                PLUS_LENGTHS_MUTTASIL,
            )
    elif nxt.has_shadda:
        emit(
            view,
            "madd_lazim_kalimi_muthaqqal",
            word,
            carrier,
            "madd letter before a shadda in the same word (6 harakat)",
        )
    elif nxt.has_sukun and MADDAH in carrier.marks:
        emit(
            view,
            "madd_lazim_kalimi_mukhaffaf",
            word,
            carrier,
            "madd letter before an original sukun in the same word (6 harakat)",
        )
    elif last_letter and stops:
        emit(
            view,
            "madd_arid_sukun",
            word,
            carrier,
            "madd letter before the last letter of a stopped word",
            PLUS_LENGTHS_ARID,
        )
    else:
        emit(view, "madd_tabii", word, carrier, "madd letter not followed by hamza or sukun")
    if preceded_by_hamza and not is_hamza(nxt):
        emit(view, "madd_badal", word, carrier, "madd letter replacing the second hamza")


def _word_final(
    view: AyahView, wi: int, word: Word, ml: MaddLetter, preceded_by_hamza: bool
) -> None:
    carrier = word.letters[ml.li]
    relation, nxt = following(view, wi, len(word.letters) - 1)
    if relation == "unknown":
        view.note_unresolved(
            "word-final madd letter at the end of the last ayah in wasl mode needs the "
            "following ayah"
        )
        return
    if relation == "stop":
        emit(view, "madd_tabii", word, carrier, "word-final madd letter at a stop")
    elif nxt is not None and is_hamza(nxt):
        emit(
            view,
            "madd_munfasil",
            word,
            carrier,
            "word-final madd letter before a hamza at the start of the next word",
            PLUS_LENGTHS_MUNFASIL,
        )
    elif nxt is not None and nxt.char == ALEF and WASL_STOP in nxt.marks:
        emit(
            view,
            "madd_letter_dropped",
            word,
            carrier,
            "madd letter meets the sakin after hamzat al-wasl: not pronounced when joined",
        )
    else:
        emit(view, "madd_tabii", word, carrier, "word-final madd letter before a moving letter")
    if preceded_by_hamza:
        emit(view, "madd_badal", word, carrier, "madd letter replacing the second hamza")


def detect_iwad_and_lin(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        if not _stops_here(view, wi):
            continue
        letters = word.letters
        last = letters[-1]
        if any(m in TANWEEN_FATH for m in last.marks) and last.char != "ة":
            emit(
                view,
                "madd_iwad",
                word,
                last,
                "tanween fatha is replaced by an alef at a stop (2 harakat)",
            )
        if len(letters) >= 3:
            lin = letters[-2]
            if lin.char in "وي" and lin.has_sukun and FATHA in letters[-3].marks:
                emit(
                    view,
                    "madd_lin",
                    word,
                    lin,
                    "sakin waw or yeh after a fatha, before the last letter of a stopped word",
                    PLUS_LENGTHS_ARID,
                )


def detect_fawatih(view: AyahView) -> None:
    if view.ayah != 1 or view.surah not in FAWATIH_SURAHS:
        return
    for word in view.words:
        letters = word.letters
        if not all(x.char in FAWATIH_LETTERS for x in letters):
            break
        for li, letter in enumerate(letters):
            nxt = letters[li + 1] if li + 1 < len(letters) else None
            if letter.char in HAY_TAHAR and MADDAH not in letter.marks:
                emit(
                    view,
                    "madd_harf_hay_tahar",
                    word,
                    letter,
                    "isolated letter of حي طهر: natural madd, 2 harakat",
                )
            elif letter.char in LAZIM_LETTERS and MADDAH in letter.marks:
                heavy = letter.char in "لس" and nxt is not None and nxt.char == MEEM
                heavy = heavy and nxt is not None and nxt.has_shadda
                rule = "madd_lazim_harfi_muthaqqal" if heavy else "madd_lazim_harfi_mukhaffaf"
                note = "isolated letter assimilated into the next one" if heavy else None
                note = note or "isolated letter of نقص عسلكم: 6 harakat"
                variants = AIN_LENGTHS if letter.char == "ع" else ()
                emit(view, rule, word, letter, note, variants)


def _pronoun_meem(word: Word, li: int) -> bool:
    """Plural pronoun meem: a final sakin meem after ha, kaf or ta with the matching vowel."""
    letters = word.letters
    if li != len(letters) - 1 or li == 0:
        return False
    meem, prev = letters[li], letters[li - 1]
    if meem.char != MEEM or not meem.has_sukun:
        return False
    return (prev.char == "ه" and (DAMMA in prev.marks or KASRA in prev.marks)) or (
        prev.char in "كت" and DAMMA in prev.marks
    )


def detect_sila(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        letters = word.letters
        for li, letter in enumerate(letters):
            if (
                li == len(letters) - 1
                and letter.char == "ه"
                and any(m in SILA_MARKS for m in letter.marks)
            ):
                relation, nxt = following(view, wi, li)
                if relation == "stop":
                    view.note_skipped("sila mark on a final ha at a stop is not pronounced")
                    continue
                if relation == "unknown":
                    view.note_unresolved(
                        "ha al-kinaya at the end of the last ayah in wasl mode needs the "
                        "following ayah"
                    )
                    continue
                if is_hamza(nxt):
                    emit(
                        view,
                        "madd_sila_kubra_ha",
                        word,
                        letter,
                        "pronoun ha lengthened before a hamza at the start of the next word",
                        PLUS_LENGTHS_MUNFASIL,
                    )
                else:
                    emit(
                        view,
                        "madd_sila_sughra_ha",
                        word,
                        letter,
                        "pronoun ha lengthened (2 harakat) before a moving letter",
                    )
            elif _pronoun_meem(word, li):
                relation, nxt = following(view, wi, li)
                if relation in ("stop", "unknown") or nxt is None:
                    if relation == "unknown":
                        view.note_unresolved(
                            "plural meem at the end of the last ayah in wasl mode needs the "
                            "following ayah"
                        )
                    continue
                if nxt.char == ALEF and WASL_STOP in nxt.marks:
                    view.note_skipped("plural meem before hamzat al-wasl takes a damma instead")
                    continue
                if is_hamza(nxt):
                    emit(
                        view,
                        "madd_sila_kubra_meem",
                        word,
                        letter,
                        "plural meem before a hamza at the start of the next word",
                        SILA_MEEM_KUBRA,
                    )
                else:
                    emit(
                        view,
                        "madd_sila_sughra_meem",
                        word,
                        letter,
                        "plural meem before a moving letter",
                        SILA_MEEM_SUGHRA,
                    )


MADD_DETECTORS = {
    **{
        r: detect_madd
        for r in (
            "madd_tabii",
            "madd_badal",
            "madd_muttasil",
            "madd_munfasil",
            "madd_muttasil_arid",
            "madd_arid_sukun",
            "madd_lazim_kalimi_muthaqqal",
            "madd_lazim_kalimi_mukhaffaf",
            "madd_letter_dropped",
        )
    },
    "madd_harf_hay_tahar": detect_fawatih,
    "madd_lazim_harfi_muthaqqal": detect_fawatih,
    "madd_lazim_harfi_mukhaffaf": detect_fawatih,
    "madd_iwad": detect_iwad_and_lin,
    "madd_lin": detect_iwad_and_lin,
    "madd_sila_sughra_ha": detect_sila,
    "madd_sila_kubra_ha": detect_sila,
    "madd_sila_sughra_meem": detect_sila,
    "madd_sila_kubra_meem": detect_sila,
}


def detect_ana(view: AyahView) -> None:
    """The alef of the pronoun ana: kept before a hamza, dropped before anything else."""
    for wi, word in enumerate(view.words):
        letters = word.letters
        if len(letters) < 3 or len(letters) > 4:
            continue
        hamza, noon, alef = letters[-3], letters[-2], letters[-1]
        if not (
            is_hamza(hamza)
            and FATHA in hamza.marks
            and noon.char == "ن"
            and FATHA in noon.marks
            and not noon.has_shadda
            and alef.char == ALEF
        ):
            continue
        if len(letters) == 4 and letters[0].char not in "وف":
            continue
        relation, nxt = following(view, wi, len(letters) - 1)
        if relation == "stop":
            view.note_skipped("the alef of ana is kept when stopping")
        elif relation == "unknown":
            view.note_unresolved("ana at the end of the last ayah in wasl mode needs the next ayah")
        elif nxt is not None and is_hamza(nxt):
            if KASRA in nxt.marks:
                emit(
                    view,
                    "alef_ana_before_hamza_kasra",
                    word,
                    alef,
                    "ana before a hamza with a kasra: two readings",
                    ("drop_alef", "keep_alef_with_separated_madd"),
                )
            else:
                emit(
                    view,
                    "alef_ana_before_hamza",
                    word,
                    alef,
                    "ana before a hamza with a fatha or damma: alef kept and lengthened",
                )
        else:
            emit(view, "alef_ana_dropped", word, alef, "ana joined to a letter that is not a hamza")


MADD_DETECTORS.update(
    {
        "alef_ana_before_hamza": detect_ana,
        "alef_ana_before_hamza_kasra": detect_ana,
        "alef_ana_dropped": detect_ana,
    }
)
