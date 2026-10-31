"""Deterministic detectors for the rules a cited source defines mechanically.

Each detector proposes candidate occurrences from the exact Qaloun text and an explicit
reading context. Nothing here verifies a ruling: a candidate is a procedure's output, not
a scholarly claim. Missing context is reported as unresolved, never guessed.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from wirdi_mcp.tajwid.text import HAMZA_FORMS, MADDAH, SMALL_HIGH_MEEM, Letter, Word

DETECTOR_VERSION = "1.0.0"

THROAT = frozenset("هعحغخ") | HAMZA_FORMS
IDGHAM_WITH_GHUNNA = frozenset("ينمو")
IDGHAM_WITHOUT_GHUNNA = frozenset("لر")
IQLAB_LETTER = "ب"
IKHFA = frozenset("صذثكجشقسدطزفتضظ")
QALQALA = frozenset("قطبجد")
SHAMSIYA = frozenset("طثصرتضذندسظزشل")
QAMARIYA = frozenset("ابغحجكوخفعقيمه") | HAMZA_FORMS
ARTICLE_PREFIXES = frozenset("وفبكلت")

NOON_SAKINA_TANWEEN_RULES = (
    "idhar_halqi",
    "idgham_bighunna",
    "idgham_bilaghunna",
    "iqlab",
    "ikhfa_haqiqi",
    "idhar_mutlaq",
)
MIM_SAKINA_RULES = ("ikhfa_shafawi", "idgham_shafawi", "idhar_shafawi")
QALQALA_RULES = ("qalqala_sughra", "qalqala_kubra")
LAM_RULES = ("lam_shamsiya", "lam_qamariya")
GHUNNA_RULES = ("ghunna_mushaddad",)


@dataclass(frozen=True)
class Occurrence:
    rule_id: str
    word_index: int
    start: int
    end: int
    note: str | None = None


@dataclass
class AyahView:
    """One ayah plus the reading context a detector may rely on."""

    words: tuple[Word, ...]
    mode: str  # "wasl" or "waqf"
    # First letter of the next ayah when the reading continues into it and it is known.
    next_ayah_first: Letter | None = None
    # True when the final word is a stop (verse end in waqf, or an explicit stop word).
    stops_at_end: bool = True
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


def _emit(view: AyahView, rule_id: str, word: Word, letter: Letter, note: str | None) -> None:
    view.occurrences.append(Occurrence(rule_id, word.index, letter.start, letter.end, note))


def _classify_by_next(next_char: str, same_word: bool, is_tanween: bool) -> tuple[str, str] | None:
    """Rule for a noon sakina / tanween followed by next_char, from the cited rule tables."""
    if next_char in THROAT:
        return "idhar_halqi", "next letter is a throat letter"
    if next_char in IDGHAM_WITH_GHUNNA:
        if same_word:
            return "idhar_mutlaq", "idgham letter in the same word"
        return "idgham_bighunna", "next word begins with one of the letters of ينمو"
    if next_char in IDGHAM_WITHOUT_GHUNNA:
        if same_word:
            return "idhar_mutlaq", "idgham letter in the same word"
        return "idgham_bilaghunna", "next word begins with lam or ra"
    if next_char == IQLAB_LETTER:
        return "iqlab", "next letter is ba"
    if next_char in IKHFA:
        return "ikhfa_haqiqi", "next letter is one of the fifteen ikhfa letters"
    return None


def detect_noon_sakina_and_tanween(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        for li, letter in enumerate(word.letters):
            tanween = letter.has_tanween and li == len(word.letters) - 1
            noon = letter.char == "ن" and not letter.has_tanween
            if noon:
                if MADDAH in letter.marks:
                    view.note_skipped("letter-name noon (maddah) is outside the cited rule scope")
                    continue
                sakina = letter.has_sukun or SMALL_HIGH_MEEM in letter.marks or letter.is_bare
                if not sakina:
                    continue
            elif not tanween:
                continue
            relation, nxt = following(view, wi, li)
            if relation == "stop":
                # Tanween and a final noon are not pronounced as such at a stop.
                if tanween:
                    view.note_skipped("tanween at a stop is dropped; no rule applies")
                continue
            if relation == "unknown":
                view.note_unresolved(
                    "word-final noon sakina or tanween at the end of the last ayah in wasl mode "
                    "needs the following ayah"
                )
                continue
            assert nxt is not None
            if relation == "same_word" and nxt.char == "ا":
                if noon and letter.is_bare:
                    view.note_skipped("bare noon before alef is not a noon sakina here")
                continue
            if relation != "same_word" and is_wasl_alef(nxt):
                view.note_skipped("next word starts with hamzat al-wasl: the noon takes a vowel")
                continue
            choice = _classify_by_next(nxt.char, relation == "same_word", tanween)
            if choice is None:
                view.note_skipped("next letter belongs to no noon sakina rule")
                continue
            rule_id, why = choice
            where = "tanween" if tanween else "noon sakina"
            _emit(view, rule_id, word, letter, f"{where}; {why}")


def detect_mim_sakina(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        for li, letter in enumerate(word.letters):
            if letter.char != "م":
                continue
            # This corpus writes the sakin mim before ba and mim without a sukun.
            if not (letter.has_sukun or (letter.is_bare and li == len(word.letters) - 1)):
                continue
            relation, nxt = following(view, wi, li)
            if relation == "stop":
                continue
            if relation == "unknown":
                view.note_unresolved(
                    "word-final mim sakina at the end of the last ayah in wasl mode "
                    "needs the following ayah"
                )
                continue
            assert nxt is not None
            if relation != "same_word" and is_wasl_alef(nxt):
                view.note_skipped("next word starts with hamzat al-wasl: the mim takes a vowel")
                continue
            if relation == "same_word" and nxt.char == "ا":
                continue
            if nxt.char == "ب":
                _emit(view, "ikhfa_shafawi", word, letter, "mim sakina before ba")
            elif nxt.char == "م":
                _emit(view, "idgham_shafawi", word, letter, "mim sakina before a moving mim")
            else:
                _emit(view, "idhar_shafawi", word, letter, "mim sakina before another letter")


def detect_ghunna_mushaddad(view: AyahView) -> None:
    for word in view.words:
        for letter in word.letters:
            if letter.char in "نم" and letter.has_shadda:
                note = "geminated noon" if letter.char == "ن" else "geminated mim"
                _emit(view, "ghunna_mushaddad", word, letter, note)


def detect_qalqala(view: AyahView) -> None:
    for wi, word in enumerate(view.words):
        last = len(word.letters) - 1
        for li, letter in enumerate(word.letters):
            if letter.char not in QALQALA:
                continue
            at_word_end = li == last
            if letter.has_sukun:
                rule = "qalqala_kubra" if at_word_end else "qalqala_sughra"
                note = "sakin letter at the end of the word" if at_word_end else "sakin mid-word"
                _emit(view, rule, word, letter, note)
            elif at_word_end and wi == len(view.words) - 1 and view.stops_at_end:
                degree = "with shadda" if letter.has_shadda else "without shadda"
                _emit(view, "qalqala_kubra", word, letter, f"final letter at a stop, {degree}")


def detect_lam(view: AyahView) -> None:
    for word in view.words:
        letters = word.letters
        for k in range(min(3, len(letters) - 2)):
            if any(x.char not in ARTICLE_PREFIXES for x in letters[:k]):
                break
            alef, lam, after = letters[k], letters[k + 1], letters[k + 2]
            if alef.char != "ا" or lam.char != "ل":
                continue
            if after.char == "ل" and len(letters) == k + 4 and letters[k + 3].char == "ه":
                view.note_skipped("lafz al-jalala is a separate rule family")
                break
            if (
                lam.is_bare
                and after.char == "ي"
                and after.has_sukun
                and len(letters) > k + 3
                and letters[k + 3].char == "ل"
            ):
                _emit(
                    view,
                    "lam_shamsiya",
                    word,
                    lam,
                    "article lam assimilated into lam; the doubled lam is not written",
                )
            elif lam.has_sukun and after.char in QAMARIYA:
                _emit(view, "lam_qamariya", word, lam, "article lam pronounced before its letter")
            elif lam.is_bare and after.char in SHAMSIYA:
                _emit(view, "lam_shamsiya", word, lam, "article lam assimilated into its letter")
            else:
                view.note_skipped("alef-lam whose marks do not fit the article pattern")
            break


Group = Callable[[AyahView], None]

# rule_id -> (group function, rule version, riwaya, tariq). One group may serve several rules.
DETECTORS: dict[str, tuple[Group, str, str, str]] = {
    **{
        r: (detect_noon_sakina_and_tanween, "1", "qaloun", "abu_nashit")
        for r in NOON_SAKINA_TANWEEN_RULES
    },
    **{r: (detect_mim_sakina, "1", "qaloun", "abu_nashit") for r in MIM_SAKINA_RULES},
    **{r: (detect_qalqala, "1", "qaloun", "abu_nashit") for r in QALQALA_RULES},
    **{r: (detect_lam, "1", "qaloun", "unspecified") for r in LAM_RULES},
    **{r: (detect_ghunna_mushaddad, "1", "qaloun", "abu_nashit") for r in GHUNNA_RULES},
}


def run_detectors(view: AyahView, rule_ids: frozenset[str] | None = None) -> None:
    groups = {fn for rid, (fn, *_rest) in DETECTORS.items() if rule_ids is None or rid in rule_ids}
    for fn in sorted(groups, key=lambda f: f.__name__):
        fn(view)
    if rule_ids is not None:
        view.occurrences[:] = [o for o in view.occurrences if o.rule_id in rule_ids]
