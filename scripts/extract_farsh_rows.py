#!/usr/bin/env python3
"""Read the farsh tables (Nabhan pp.111-198) from the LOCAL PDF into a git-ignored JSON file.

Each table row has four cells: the ayah number (Kufian), the Hafs word, a short description of the
Qaloun change and the Qaloun word. The text layer of the PDF is out of order, so the rows are
rebuilt from
the position of each glyph (`pdftotext -bbox-layout`): the cell is chosen by the x position, and
a word of the description comes out reversed and is turned back. The output is a working file for
cross-checks against the corpus; it is not book text to publish and is never committed
(`knowledge/sources/*/pages*` and `.work/` are ignored).

Usage: extract_farsh_rows.py [--pdf PDF] [--out JSON]  (defaults: the local PDF in docs/, the
thamar-yani-2003 folder of knowledge/sources/)
"""

import argparse
import html
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

FIRST_PAGE, LAST_PAGE = 111, 198
SURAH_NAMES = (
    "الفاتحة البقرة آل عمران النساء المائدة الأنعام الأعراف الأنفال التوبة يونس هود يوسف الرعد "
    "إبراهيم الحجر النحل الإسراء الكهف مريم طه الأنبياء الحج المؤمنون النور الفرقان الشعراء النمل "
    "القصص العنكبوت الروم لقمان السجدة الأحزاب سبأ فاطر يس الصافات ص الزمر غافر فصلت الشورى "
    "الزخرف الدخان الجاثية الأحقاف محمد الفتح الحجرات ق الذاريات الطور النجم القمر الرحمن "
    "الواقعة الحديد المجادلة الحشر الممتحنة الصف الجمعة المنافقون التغابن الطلاق التحريم الملك "
    "القلم الحاقة المعارج نوح الجن المزمل المدثر القيامة الإنسان المرسلات النبأ النازعات عبس "
    "التكوير الانفطار المطففين الانشقاق البروج الطارق الأعلى الغاشية الفجر البلد الشمس الليل "
    "الضحى الشرح التين العلق القدر البينة الزلزلة العاديات القارعة التكاثر العصر الهمزة الفيل "
    "قريش الماعون الكوثر الكافرون النصر المسد الإخلاص الفلق الناس"
).split()
# two-word names are glued back with their space removed when compared
SURAH_KEYS = None
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
WORD = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>'
)
MARKS = re.compile("[\u064b-\u065f\u0670\u06d6-\u06ed\u0640\ue000-\uf8ff]")


def page_words(pdf: Path, page: int) -> list[tuple[float, float, float, str]]:
    xml = subprocess.run(
        ["pdftotext", "-bbox-layout", "-f", str(page), "-l", str(page), str(pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    out = []
    for x0, y0, x1, _y1, text in WORD.findall(xml):
        out.append(
            (float(x0), float(y0), float(x1), unicodedata.normalize("NFKC", html.unescape(text)))
        )
    return out


def lines_of(words, tolerance=2.5):
    lines: list[list] = []
    for x0, y0, x1, text in sorted(words, key=lambda w: (round(w[1]), -w[0])):
        for line in lines:
            if abs(line[0] - y0) <= tolerance:
                line[1].append((x0, x1, text))
                break
        else:
            lines.append([y0, [(x0, x1, text)]])
    return lines


def logical(tokens) -> str:
    """Tokens of one cell, right to left, each multi-letter token turned back."""
    parts = []
    for _x0, _x1, text in sorted(tokens, key=lambda t: -t[0]):
        letters = MARKS.sub("", text)
        parts.append(text[::-1] if len(letters) >= 2 else text)
    return " ".join(p for p in parts if p.strip())


def base_letters(tokens) -> str:
    """The base letters of a word cell in reading order, a space where the glyphs leave a gap."""
    out: list[str] = []
    previous_left = None
    for x0, x1, text in sorted(tokens, key=lambda t: -t[0]):
        letters = MARKS.sub("", text).replace(" ", "")
        if not letters:
            continue
        if previous_left is not None and previous_left - x1 > 2.5:
            out.append(" ")
        out.append(letters[::-1] if len(letters) >= 2 else letters)
        previous_left = x0 if previous_left is None else min(previous_left, x0)
    return "".join(out).strip()


def _fold(text: str) -> str:
    text = MARKS.sub("", text)
    text = re.sub("[أإآٱ]", "ا", text).replace("ى", "ي").replace("ة", "ه")
    return re.sub("[^\u0621-\u064a]", "", text).removeprefix("ال")


def _key(text: str) -> str:
    """Letters other than alef and lam, unordered: the extraction swaps a lam-alef ligature."""
    return "".join(sorted(c for c in _fold(text) if c not in "ال"))


def surah_number(heading: str, current: int | None = None) -> int | None:
    global SURAH_KEYS
    if SURAH_KEYS is None:
        names = []
        i = 0
        merged = []
        while i < len(SURAH_NAMES):
            if SURAH_NAMES[i] == "آل":
                merged.append("آل عمران")
                i += 2
            else:
                merged.append(SURAH_NAMES[i])
                i += 1
        SURAH_KEYS = [_key(n) for n in merged]
        assert len(SURAH_KEYS) == 114, len(SURAH_KEYS)
        del names
    key = _key(heading)
    # the tables follow the order of the mushaf, which settles the few names that fold together
    candidates = [i + 1 for i, k in enumerate(SURAH_KEYS) if k == key and i + 1 >= (current or 1)]
    return candidates[0] if candidates else None


def heading_surah(tokens, current: int | None = None) -> int | None:
    """A heading line is the word سورة (extracted reversed) and a name, with no digit."""
    ordered = [t[2] for t in sorted(tokens, key=lambda t: -t[0])]
    if not ordered or ordered[0] != "ةروس" or any(ch.isdigit() for t in ordered for ch in t):
        return None
    # the name may be followed by words such as « عليهم السلام »: try the longest name first
    for count in range(len(ordered) - 1, 0, -1):
        name = "".join(t[::-1] if len(MARKS.sub("", t)) >= 2 else t for t in ordered[1 : 1 + count])
        found = surah_number(name, current)
        if found is not None:
            return found
    return None


def parse_page(words, state: dict) -> list[dict]:
    if not words:
        return []
    left, right = min(w[0] for w in words), max(w[2] for w in words)
    # column edges measured on the page: ayah | Hafs | description | Qaloun, right to left
    edges = tuple(left + f * (right - left) for f in (0.90, 0.70, 0.21))
    rows: list[dict] = []
    for _y0, tokens in lines_of(words):
        found = heading_surah(tokens, state["surah"])
        if found is not None:
            state["surah"] = found
            continue
        cells = {"ayah": [], "hafs": [], "desc": [], "qaloun": []}
        for x0, x1, t in tokens:
            mid = (x0 + x1) / 2
            key = (
                "ayah"
                if mid > edges[0]
                else "hafs"
                if mid > edges[1]
                else "desc"
                if mid > edges[2]
                else "qaloun"
            )
            cells[key].append((x0, x1, t))
        number = "".join(t for _a, _b, t in cells["ayah"]).translate(ARABIC_DIGITS)
        numbers = re.findall(r"\d+", number)
        if numbers:
            rows.append(
                {
                    "surah": state["surah"],
                    "ayah": [int(n) for n in numbers],
                    "hafs": base_letters(cells["hafs"]),
                    "desc": logical(cells["desc"]),
                    "qaloun": base_letters(cells["qaloun"]),
                }
            )
        elif rows and any(cells.values()):
            last = rows[-1]
            last["desc"] = (last["desc"] + " " + logical(cells["desc"])).strip()
            last["hafs"] = (last["hafs"] + " " + base_letters(cells["hafs"])).strip()
            last["qaloun"] = (last["qaloun"] + " " + base_letters(cells["qaloun"])).strip()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=ROOT / "docs" / "Quraan01260.pdf")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "knowledge" / "sources" / "thamar-yani-2003" / "farsh_rows.json",
    )
    args = parser.parse_args()
    result = []
    state = {"surah": None}
    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        for row in parse_page(page_words(args.pdf, page), state):
            row["page"] = page
            result.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(result)} rows from pages {FIRST_PAGE}-{LAST_PAGE} written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
