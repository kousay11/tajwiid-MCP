"""Static letter data from Book A pp.40-45: places of articulation and characteristics.

Pure data, no corpus access. The tables follow the book's own mnemonics. Alef is the
long-vowel letter of the open space (jawf) and hamza is counted separately, so there are 29
letters. Nothing here is scholarly reviewed.
"""

from dataclasses import dataclass

ALL_LETTERS = "ءابتثجحخدذرزسشصضطظعغفقكلمنهوي"

# makhraj: letter -> (region, place). Seventeen places in five regions (Book A p.40-41).
_PLACES = (
    ("jawf", "open_space", "ا"),
    ("throat", "deepest_throat", "ءه"),
    ("throat", "middle_throat", "عح"),
    ("throat", "nearest_throat", "غخ"),
    ("tongue", "back_of_tongue_raised", "ق"),
    ("tongue", "back_of_tongue_lowered", "ك"),
    ("tongue", "middle_of_tongue", "جشي"),
    ("tongue", "edge_of_tongue", "ض"),
    ("tongue", "tongue_edge_after_dad", "ل"),
    ("tongue", "tongue_tip_noon", "ن"),
    ("tongue", "tongue_tip_ra", "ر"),
    ("tongue", "tongue_tip_upper_roots", "دتط"),
    ("tongue", "tongue_tip_asal", "سصز"),
    ("tongue", "tongue_tip_upper_incisors", "ثذظ"),
    ("lips", "lower_lip_and_upper_teeth", "ف"),
    ("lips", "both_lips", "بمو"),
    ("nasal_cavity", "khayshum", ""),  # the ghunna has no letter of its own
)
MAKHRAJ = {letter: (region, place) for region, place, letters in _PLACES for letter in letters}

HAMS = frozenset("فحثهشخصسكت")  # فحثه شخص سكت
SHIDDA = frozenset("ءجدقطبكت")  # أجد قط بكت
BAYNIYYA = frozenset("لنعمر")  # لن عمر
ISTIALA = frozenset("خصضغطقظ")  # خص ضغط قظ
ITBAQ = frozenset("صضطظ")
IDHLAQ = frozenset("فرمنلب")  # فر من لب
SAFIR = frozenset("صسز")
QALQALA = frozenset("قطبجد")  # قطب جد
INHIRAF = frozenset("لر")
TAKRIR = frozenset("ر")
TAFASHSHI = frozenset("ش")
ISTITALA = frozenset("ض")


@dataclass(frozen=True)
class LetterData:
    letter: str
    region: str
    place: str
    paired: tuple[str, ...]  # one characteristic from each opposed pair
    other: tuple[str, ...]


def properties(letter: str) -> LetterData:
    region, place = MAKHRAJ[letter]
    paired = (
        "hams" if letter in HAMS else "jahr",
        "shidda" if letter in SHIDDA else "bayniyya" if letter in BAYNIYYA else "rakhawa",
        "istiala" if letter in ISTIALA else "istifal",
        "itbaq" if letter in ITBAQ else "infitah",
        "idhlaq" if letter in IDHLAQ else "ismat",
    )
    other = tuple(
        name
        for name, members in (
            ("safir", SAFIR),
            ("qalqala", QALQALA),
            ("inhiraf", INHIRAF),
            ("takrir", TAKRIR),
            ("tafashshi", TAFASHSHI),
            ("istitala", ISTITALA),
        )
        if letter in members
    )
    if letter in "وي":
        other += ("lin_when_sakin_after_fatha",)
    return LetterData(letter, region, place, paired, other)


def normalize_letter(char: str) -> str | None:
    if char in "أإؤئ":
        return "ء"
    if char in ("آ",):
        return None
    if char in ("ى", "ے"):
        return "ي"
    if char == "ة":
        return "ت"
    return char if char in ALL_LETTERS else None
