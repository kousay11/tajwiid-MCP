#!/usr/bin/env python3
"""Add the second citation (the longer book Nabhan, which Book A digests) to the rule records.

Idempotent. Run after scripts/build_book_a_rules.py and before scripts/build_rule_manifest.py.
Each page was read on its image. The longer book agrees with Book A on every rule listed here, so
the citation records where the text is found, not an independent confirmation, and the rule says
so in its limitations. The longer book names Abu Nashit only on p.111 (heading of the farsh
tables), so no rule's tariq changes.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_book_a_rules import NABHAN  # noqa: E402

LIMIT = (
    "Second citation: the longer book Nabhan, which Book A digests. It agrees with the "
    "paraphrase, so it shows where the text is found, not an independent confirmation."
)
PAGES = {
    "idhar_halqi": (11, 12),
    "idgham_bighunna": (12, 13),
    "idgham_bilaghunna": (13,),
    "idhar_mutlaq": (13, 14),
    "iqlab": (14,),
    "ikhfa_haqiqi": (15, 16),
    "idgham_shafawi": (17,),
    "ikhfa_shafawi": (17,),
    "idhar_shafawi": (18,),
    "ghunna_mushaddad": (19, 21),
    "lam_shamsiya": (21, 22),
    "lam_qamariya": (22, 23),
    "qalqala": (60,),
    "madd_tabii": (25,),
    "madd_badal": (26,),
    "hamza_wasl_then_qat_in_word": (26, 27),
    "madd_iwad": (27,),
    "noon_tawkid_khafifa_stop": (28,),
    "madd_harf_hay_tahar": (28,),
    "madd_sila_sughra_meem": (29,),
    "madd_sila_sughra_ha": (29, 30),
    "madd_sila_ha_exception": (30, 31, 33),
    "madd_muttasil": (31, 32),
    "madd_munfasil": (32,),
    "madd_sila_kubra_meem": (32, 33),
    "madd_sila_kubra_ha": (33,),
    "madd_arid_sukun": (33,),
    "madd_muttasil_arid": (34,),
    "madd_lin": (34,),
    "madd_lazim_kalimi_muthaqqal": (35,),
    "madd_lazim_kalimi_mukhaffaf": (35, 36),
    "madd_lazim_harfi_muthaqqal": (37,),
    "madd_lazim_harfi_mukhaffaf": (36, 37),
    "madd_alif_lam_mim_imran": (37,),
    "alef_ana_before_hamza": (39,),
    "alef_ana_before_hamza_kasra": (39,),
    "alef_ana_dropped": (39,),
    "alef_thabita": (39, 40),
    "madd_letter_dropped": (40,),
    "hamza_ibdal_yajuj": (41,),
    "hamza_ibdal_ruya": (41,),
    "hamza_ibdal_minsaa": (42,),
    "hamza_ibdal_saala": (42,),
    "hamza_ibdal_musada": (42,),
    "hamza_waw_huzu_kufu": (42,),
    "hamza_nabi": (42,),
    "hamza_nabi_exception": (42,),
    "hamza_double_in_word": (43,),
    "hamza_double_exception": (43,),
    "hamza_arayta_tashil": (44,),
    "hamza_istifham_added": (44,),
    "istifham_repeated_first": (44, 45),
    "istifham_repeated_second": (45,),
    "hamza_two_words_same": (45, 46),
    "hamza_two_words_different": (46, 47),
    "hamzat_wasl_article": (48, 50),
    "hamzat_wasl_noun": (48,),
    "hamzat_wasl_verb": (49, 50),
    "sakin_before_hamzat_wasl": (51,),
    "alef_tafkhim": (65, 69),
    "istiala_rank_1": (65,),
    "istiala_rank_2": (65, 66),
    "istiala_rank_3": (66,),
    "istiala_rank_4": (66,),
    "ra_tafkhim": (66, 67),
    "ra_tarqiq": (67,),
    "ra_jawaz": (67,),
    "ra_mutatarrif_tafkhim": (68,),
    "ra_mutatarrif_tarqiq": (68,),
    "ra_mutatarrif_jawaz": (68,),
    "lam_jalala_tafkhim": (69,),
    "lam_jalala_tarqiq": (69,),
    "alef_tafkhim_after_ra": (69,),
    "alef_tarqiq": (69,),
    "taqlil_tawrat": (69,),
    "imala_har": (70,),
    "ghunna_tafkhim": (70,),
    "ghunna_tarqiq": (70,),
    "idgham_kabir_mutamathil": (71,),
    "idgham_mutamathilayn": (71, 72),
    "idgham_mutajanisayn": (72, 73, 74),
    "idgham_mutaqaribayn": (74,),
    "idgham_naqis": (75,),
    "ya_idafa_fath": (77, 78),
    "ya_idafa_iskan_exception": (77, 78),
    "ya_idafa_rabbi_two_readings": (78,),
    "ya_idafa_iskan_before_letter": (79,),
    "ya_idafa_maee": (79,),
}


def walk(node, pages: tuple[int, ...]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "evidence" and isinstance(value, list):
                value[:] = [c for c in value if c.get("edition_id") != NABHAN["edition_id"]]
                value.extend({**NABHAN, "locator": f"p.{p}"} for p in pages)
            else:
                walk(value, pages)
    elif isinstance(node, list):
        for item in node:
            walk(item, pages)


def main() -> int:
    root = ROOT / "knowledge" / "rules"
    done = 0
    for rule_id, pages in PAGES.items():
        path = root / rule_id / "1.json"
        rule = json.loads(path.read_text(encoding="utf-8"))
        walk(rule, pages)
        rule["limitations"] = [x for x in rule["limitations"] if x != LIMIT] + [LIMIT]
        path.write_text(json.dumps(rule, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        done += 1
    print(f"{done} rule records carry a second citation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
