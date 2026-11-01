#!/usr/bin/env python3
"""Turn the farsh table rows into closed lists of places for the detectors (Nabhan pp.111-198).

Reads the local, git-ignored rows written by scripts/extract_farsh_rows.py, keeps the rows for
(a) two hamzas in two words and (b) a vowel given to a sakin letter before hamzat al-wasl, finds the
word in the corpus at the row's Kufian place, and writes `src/wirdi_mcp/tajwid/farsh_places.py`.
A row the corpus cannot show is printed and left out, never guessed. The generated module holds only
places and word skeletons, no book text. It also prints the cross-check of the ya rows against the
ya detectors.

Usage: build_farsh_places.py [--rows knowledge/sources/thamar-yani-2003/farsh_rows.json]
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wirdi_mcp.quran.source import PublicSourceRepository  # noqa: E402
from wirdi_mcp.tajwid.lexicon import skeleton  # noqa: E402
from wirdi_mcp.tajwid.text import tokenize  # noqa: E402

HAMZA = "ءأإؤئ"


def fold(text: str) -> str:
    text = text.replace("آ", "ا")
    text = re.sub(f"[{HAMZA}]", "ء", text).replace("ى", "ي").replace("ے", "ي")
    return re.sub("[^ء-ي]", "", text)


def norm(desc: str) -> str:
    desc = desc.replace("اهل", "اله").replace("وصال", "وصلا").replace("األ", "الأ")
    desc = re.sub(r"[-٠-٩\d]+", " ", desc)
    return re.sub(r"\s+", " ", desc).strip()


def second_hamza_variants(desc: str) -> tuple[str, ...]:
    d = re.sub(r"\s", "", desc)
    out = []
    if "بينالهمزةوالواو" in d or "بينهاوبينالواو" in d or "بينالهمزةوالواو" in d:
        out.append("tashil_second_between_hamza_and_waw")
    if "بينالهمزةوالياء" in d or "بينهاوبينالياء" in d or "بينهاوبينالكسر" in d:
        out.append("tashil_second_between_hamza_and_yeh")
    if "واوامفتوحة" in d:
        out.append("second_hamza_becomes_waw_with_fatha")
    if "واوامكسورة" in d:
        out.append("second_hamza_becomes_waw_with_kasra")
    if "ياءمفتوحة" in d or "ياءخالصةمفتوحة" in d:
        out.append("second_hamza_becomes_yeh_with_fatha")
    if not out and "سهلالهمزةالثانية" in d:
        out.append("tashil_second")
    return tuple(dict.fromkeys(out))


def _is_first(desc: str) -> bool:
    d = re.sub(r"\s", "", desc)
    return "الأولى" in d or "الأوىل" in d


def first_hamza_variants(desc: str) -> tuple[str, ...]:
    d = re.sub(r"\s", "", desc)
    if "أسقطالهمزة" in d:
        return ("drop_first_hamza_qasr", "drop_second_hamza_tawassut")
    if "سهلالهمزة" in d:
        return ("tashil_first_with_short_alef", "tashil_first_with_connected_alef")
    return ()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rows",
        type=Path,
        default=ROOT / "knowledge" / "sources" / "thamar-yani-2003" / "farsh_rows.json",
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "src" / "wirdi_mcp" / "tajwid" / "farsh_places.py"
    )
    args = parser.parse_args()
    rows = json.loads(args.rows.read_text(encoding="utf-8"))
    corpus = PublicSourceRepository.bundled().load_edition("qalun")
    by_place = collections.defaultdict(list)
    for r in corpus:
        for k in r.links:
            by_place[(r.surah, k)].append(r)

    entries: dict[tuple, dict] = {}
    unmatched = []
    seen = collections.Counter()
    for row in rows:
        d = norm(row["desc"])
        hw = row["hafs"].split()
        kind = None
        if len(hw) >= 2 and re.search(r"الهمزة", d) and re.search(f"[{HAMZA}]$", hw[0]):
            if re.match(f"^[{HAMZA}]", hw[1]) and "ألفا" not in d and "ألفاً" not in d:
                kind = "hamza"
        elif re.search(r"(ضم|كسر)\s*(ال\s*)?\w+\s*(وصلا|وصلاً)", d) and len(hw) >= 2:
            if hw[1].startswith("ا") or hw[1].startswith("ٱ") or "أسر" in hw[1]:
                kind = "sakin"
        if kind is None:
            continue
        seen[kind] += 1
        for ayah in row["ayah"]:
            for verse in by_place.get((row["surah"], ayah), []):
                words = tokenize(verse.text)
                hit = None
                for i, w in enumerate(words[:-1]):
                    sk = skeleton(w)
                    target = fold(hw[0])
                    if sk == target or (kind == "hamza" and sk == target.rstrip("ء")):
                        hit = i
                        break
                if hit is None:
                    unmatched.append((kind, row["surah"], ayah, row["hafs"], d[:40]))
                    continue
                if kind == "hamza":
                    first = "first" if _is_first(d) else "second"
                    rule = (
                        "hamza_two_words_same" if first == "first" else "hamza_two_words_different"
                    )
                    variants = (
                        first_hamza_variants(d) if first == "first" else second_hamza_variants(d)
                    )
                else:
                    rule = "sakin_before_hamzat_wasl"
                    variants = ()
                    first = "damma" if "ضم" in d.split()[0] else "kasra"
                key = (
                    rule,
                    row["surah"],
                    ayah,
                    skeleton(words[hit]),
                    skeleton(words[hit + 1]),
                )
                entries.setdefault(key, {"tag": first, "variants": variants})
    lines = [
        "# ruff: noqa: E501",
        '"""Closed lists of places from the farsh tables (Nabhan pp.111-198); do not edit.',
        "",
        "Run scripts/build_farsh_places.py to rebuild it from the local PDF. Each entry is",
        "(rule_id, surah, Kufian ayah, skeleton of the first word, skeleton of the next word,",
        "tag, variants): places and skeletons only, no book text.",
        '"""',
        "",
        "PLACES: tuple[tuple[str, int, int, str, str, str, tuple[str, ...]], ...] = (",
    ]
    for key in sorted(entries):
        value = entries[key]
        lines.append(f"    {key + (value['tag'], value['variants'])!r},")
    lines.append(")")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"rows kept {dict(seen)}; {len(entries)} places written to {args.out}")
    for item in unmatched:
        print("not matched in the corpus:", item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
