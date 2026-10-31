#!/usr/bin/env python3
# ruff: noqa: E501
"""Write the paraphrased Book A rule records (madd, hamza, tafkhim and tarqiq, taqlil).

Idempotent: rewrites knowledge/rules/<id>/1.json from the table below, then run
scripts/build_rule_manifest.py. Every record cites Book A by printed page and is unreviewed.
The definitions are short paraphrases written for this project, not quotations.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wirdi_mcp.domain.models import Citation  # noqa: E402
from wirdi_mcp.knowledge.models import RuleClause, TajwidRule  # noqa: E402

BOOK_A = {
    "source_id": "book-a",
    "edition_id": "book-a-2010",
    "title": "أحكام رواية قالون عن نافع المدني، شرح مبسط مع الأمثلة",
    "responsible_party": "جنوى توفيق (PDF author field: NAJWA)",
    "publication": "Benghazi, Libya, 1431 H / 2010",
    "riwaya": "qaloun",
    "tariq": "unspecified",
    "provenance_version": (
        "sha256:cc504928a9e07f255e9cfb0dd552866f6fe63094d79f5311b96b68dd39c64ad6"
    ),
    "validation_status": "unreviewed",
    "uri": None,
}
COMMON_LIMITATIONS = (
    "Paraphrase of the cited pages by an automated drafter; not scholarly reviewed.",
    "Only Book A is cited; the printed page is where the section begins and needs proofreading.",
)
FAMILY_ID = {
    "madd": "madd",
    "hamza": "hamza",
    "tafkhim": "tafkhim_tarqiq",
    "imala": "imala_taqlil",
    "idgham": "idgham_general",
    "yaat": "ya_idafa",
}

# rule_id: (family, name_ar, detectability, pages, definition, conditions, exceptions, limits)
RULES: dict[str, tuple] = {
    "alef_thabita": (
        "madd",
        "الألفات الثابتة وقفا ووصلا",
        "C",
        ("p.23", "p.24"),
        "Four alefs are kept both when stopping and when joining: the alef of لكنا in al-Kahf 38 "
        "and those of الظنونا، الرسولا، السبيلا in al-Ahzab 10, 66 and 67.",
        (("words", "The words are the four named, at the named places."),),
        (),
        ("A closed list in the Kufian numbering used by the book.",),
    ),
    "alef_ana_before_hamza": (
        "madd",
        "ألف أنا قبل همزة مفتوحة أو مضمومة",
        "B",
        ("p.23", "p.24"),
        "The alef of the pronoun أنا is kept and lengthened like the separated madd when the next "
        "word begins with a hamza that has a fatha or a damma.",
        (("hamza_next", "The next word begins with a hamza with a fatha or a damma."),),
        (),
        (
            "Wasl only; at a stop the alef is always kept. The lengths are those of the separated madd, as the book says (p.24).",
        ),
    ),
    "alef_ana_before_hamza_kasra": (
        "madd",
        "ألف أنا قبل همزة مكسورة",
        "B",
        ("p.24",),
        "Before a hamza with a kasra the alef of أنا has two readings: dropped, or kept with the "
        "separated madd.",
        (("hamza_next", "The next word begins with a hamza with a kasra."),),
        (),
        ("Both readings are listed in `variants`; the engine does not choose.",),
    ),
    "alef_ana_dropped": (
        "madd",
        "حذف ألف أنا وصلا",
        "B",
        ("p.23", "p.24"),
        "The alef of أنا is not pronounced when joined to a following word that does not begin "
        "with a hamza; it is pronounced when stopping.",
        (("joined", "The reading continues into a word that does not begin with a hamza."),),
        (),
        ("Wasl only.",),
    ),
    "madd_sila_ha_exception": (
        "madd",
        "كلمات استثنيت من صلة هاء الضمير",
        "C",
        ("p.18", "p.19", "p.20"),
        "Words where the pronoun ha meets the conditions for the lengthening but is read with a "
        "kasra and no lengthening: نؤته، نوله، نصله، أرجه، يتقه، يؤده, and two words that carry "
        "`variants` instead: يأته (kasra without the lengthening, or the sila; p.19 item 6) and "
        "فألقه (p.19 item 7 gives kasra with the sila, p.20 gives kasra without it).",
        (("words", "The word is one of the listed words."),),
        (),
        (
            "Matched on the spelling; any occurrence is reported.",
            "فألقه: Book A contradicts itself between p.19 item 7 (kasra with the sila) and p.20 "
            "(kasra without the sila). Both readings are listed in `variants`; none is chosen.",
            "يأته: p.19 item 6 gives two readings, kasra without the sila and the sila; both are "
            "listed in `variants`.",
        ),
    ),
    "hamza_istifham_added": (
        "hamza",
        "همزة الاستفهام المزيدة في ءامنتم وءأله",
        "C",
        ("p.27",),
        "In ءامنتم (al-A'raf 123, Ta-Ha 71, ash-Shu'ara 49) an interrogative hamza is added and the "
        "second hamza is softened with no alef between them; in ءأله in az-Zukhruf 58 the second "
        "hamza is softened.",
        (("places", "The words at the four named places."),),
        (),
        ("A closed list in the Kufian numbering used by the book.",),
    ),
    "istifham_repeated_first": (
        "hamza",
        "الاستفهام المكرر: ما أثبتت همزته في الأول",
        "C",
        ("p.27",),
        "In nine places the interrogative hamza is kept in the first clause and dropped in the "
        "second (al-Ra'd 5, al-Isra' 49 and 98, al-Mu'minun 82, as-Sajda 10, as-Saffat 16 and 53, "
        "al-Waqi'a 47, an-Nazi'at 10-11).",
        (("places", "The ayah is one of the nine places."),),
        (),
        (
            "Verse-level: anchored on the ayah's first word. A Kufian ayah split in the Qaloun "
            "count flags each part.",
        ),
    ),
    "istifham_repeated_second": (
        "hamza",
        "الاستفهام المكرر: ما أثبتت همزته في الثاني",
        "C",
        ("p.27",),
        "In two places (an-Naml 67 and al-'Ankabut 28-29) the interrogative hamza is dropped in the "
        "first clause and kept in the second.",
        (("places", "The ayah is one of the places."),),
        (),
        (
            "Verse-level: anchored on the ayah's first word. A Kufian ayah split in the Qaloun "
            "count flags each part.",
        ),
    ),
    "idgham_kabir_mutamathil": (
        "idgham",
        "الإدغام الكبير المتماثل",
        "C",
        ("p.36",),
        "Qaloun has one great idgham of identical letters: the noon of تأمنا (Yusuf 11) merges "
        "into the following noon, with a hint of the damma (ishmam) or an incomplete damma "
        "(ikhtilas).",
        (("place", "The word تأمنا in Yusuf 11."),),
        (),
        ("The book also gives two ways to read it; they are not listed here.",),
    ),
    "idgham_mutamathilayn": (
        "idgham",
        "إدغام المتماثلين",
        "A",
        ("p.36",),
        "A sakin letter merges into an identical letter that follows it (for example قد دخلوا, "
        "ربحت تجارتهم); the waw and yeh of madd are not merged.",
        (
            (
                "identical",
                "The first letter has no sign and the next letter, the same, has a shadda.",
            ),
        ),
        (),
        ("The article lam and the meem-meem case are handled by other rules.",),
    ),
    "idgham_mutajanisayn": (
        "idgham",
        "إدغام المتجانسين",
        "A",
        ("p.36", "p.37"),
        "A sakin letter merges into a letter of the same place but different quality: ت/ط, ط/ت, "
        "ت/د, د/ت, ث/ذ, ذ/ظ, ب/م.",
        (("pair", "The pair is one of the seven listed and the second letter has a shadda."),),
        (),
        ("Some pairs have a second reading with the letters kept apart.",),
    ),
    "idgham_mutaqaribayn": (
        "idgham",
        "إدغام المتقاربين",
        "A",
        ("p.38",),
        "A sakin letter merges into a letter close to it in place and quality: ل/ر, ق/ك, ذ/ت "
        "(in the forms of أخذ and اتخذ).",
        (("pair", "The pair is one of the three listed and the second letter has a shadda."),),
        (),
        ("The noon pairs are covered by the noon rules.",),
    ),
    "idgham_naqis": (
        "idgham",
        "الإدغام الناقص",
        "C",
        ("p.38", "p.39"),
        "In بسطت، فرطتم، فرطت، أحطت the ط merges into the ت but keeps its own quality, with no "
        "bounce, and the ق of نخلقكم may merge completely into the ك.",
        (("words", "The word is one of the listed words."),),
        (),
        ("The ق/ك case is a variant of a word that is not listed here.",),
    ),
    "ya_idafa_fath": (
        "yaat",
        "فتح ياء الإضافة قبل الهمزة",
        "B",
        ("p.45", "p.46", "p.48", "p.49", "p.50"),
        "Qaloun opens (fatha) the first-person ya before every hamza qat' and before hamzat "
        "al-wasl, with the exceptions in the next record.",
        (
            (
                "before_hamza_or_wasl",
                "A first-person ya follows a kasra and the next word begins with a hamza or hamzat al-wasl.",
            ),
        ),
        (("closed_ya", "Words listed in `ya_idafa_iskan_exception` are closed."),),
        (
            "Recognised from the open ya the corpus spells with a fatha; the third-person pronoun هي is skipped.",
            "Book A p.47 item 1 gives « عهدي الظالمين » at al-Baqara 144; the word is in the Kufian "
            "ayah 2:124 in the corpus and not in 2:144. The number is the book's error and has no "
            "effect here, since this rule is read from the spelling and not from a place.",
        ),
    ),
    "ya_idafa_iskan_exception": (
        "yaat",
        "ياءات الإضافة الساكنة استثناء",
        "C",
        ("p.46", "p.48", "p.49"),
        "First-person ya read with sukun although it precedes a hamza or hamzat al-wasl: eight "
        "words before a fatha hamza (فاذكروني، أرني، تفتني، ترحمني، فاتبعني، أوزعني ×2، ذروني، "
        "ادعوني), eight before a kasra hamza (أنظرني، يدعونني، إخوتي، فأنظرني ×2، يصدقني، "
        "تدعونني ×2، ذريتي، أخرتني), two before a damma hamza (بعهدي، آتوني), and three "
        "before hamzat al-wasl with no article (إني، أخي، ليتني).",
        (
            (
                "words",
                "The word is one of the listed words at its named place, before the hamza or wasl the class names.",
            ),
        ),
        (),
        (
            "A closed list in the Kufian numbering used by the book.",
            "The book disagrees with itself on four places. Each word was looked up in the corpus: "
            "(1) تدعونني: p.46 item 13 gives Ghafir 43 only, p.49 item 6 gives 41 and 43; the word "
            "is in both, both are kept. (2) أنظرني: p.46 item 6 gives al-A'raf 40, p.49 item 1 gives "
            "14; the word is in 7:14 only, 7:14 is kept. (3) فأنظرني: p.46 item 6 gives Sad 79, "
            "p.49 item 4 gives Sad 147, which does not exist; the word is in 38:79, kept. "
            "(4) أوزعني: p.49 item 6 gives al-Ahqaf 14; the word is in 46:15, with ذريتي (p.46 item "
            "15), and not in 46:14, so 46:15 is kept. The count of 21 on p.46 lists only 20 places "
            "because of (1).",
        ),
    ),
    "ya_idafa_fath_exception": (
        "yaat",
        "ياءات الإضافة المفتوحة استثناء",
        "C",
        ("p.50",),
        "Before a letter that is not a hamza the first-person ya is closed (sukun), except in five "
        "words where it is opened: بيتي (al-Baqara 125, al-Hajj 26), وجهي (al-An'am 79), مماتي "
        "(al-An'am 162), مالي (Ya-Sin 22), لي (al-Kafirun 6).",
        (("words", "The word is one of the listed words at its named place."),),
        (),
        ("A closed list in the Kufian numbering used by the book.",),
    ),
    "ya_idafa_iskan_before_letter": (
        "yaat",
        "ياءات الإضافة الساكنة قبل الحروف",
        "C",
        ("p.47",),
        "Before an ordinary letter the first-person ya is closed; Book A names seven examples: "
        "ومحياي (al-An'am 162), وما كان لي عليكم (Ibrahim 22), ولي فيها (Ta-Ha 18), مالي لا أرى "
        "(an-Naml 20), ولي نعجة (Sad 23), ما كان لي من علم (Sad 69), بيتي مؤمنا (Nuh 28).",
        (("words", "The word is one of the seven, at its named place, before the named word."),),
        (),
        (
            "A closed list in the Kufian numbering used by the book. The default (closed before an "
            "ordinary letter) is not detected beyond these seven.",
        ),
    ),
    "ya_idafa_maee": (
        "yaat",
        "ياء الإضافة في كلمة معي",
        "C",
        ("p.47",),
        "Book A's last sentence on this page says the ya of معي is open wherever it occurs, "
        "provided no hamza qat' with a fatha follows. The corpus spells the opposite: closed "
        "everywhere except before a fatha hamza (9:83 and 67:28 in the Kufian count).",
        (("word", "The word is معي, with or without a one-letter prefix."),),
        (),
        (
            "Not arbitrated: the sentence contradicts both the corpus spelling and the book's own "
            "classes 1 and 6 on pp.48-50, which give the reverse. Each occurrence reports what the "
            "corpus spells and nothing is chosen.",
        ),
    ),
    "ya_idafa_rabbi_two_readings": (
        "yaat",
        "ياء ربي في فصلت",
        "C",
        ("p.46",),
        "The ya of ربي in Fussilat 50 (إن لي عنده للحسنى) may be read with fatha or sukun; the "
        "fatha is the reading put first in teaching.",
        (("place", "The word ربي in Fussilat 50."),),
        (),
        ("One place.",),
    ),
    "madd_tabii": (
        "madd",
        "المد الطبيعي",
        "A",
        ("p.14", "p.15"),
        "The natural madd lengthens an alef after a fatha, a waw after a damma or a yeh after "
        "a kasra by two harakat, when no hamza, sukun or shadda follows it.",
        (
            ("letter", "A madd letter (alef, waw or yeh) matching the vowel before it."),
            ("no_cause", "No hamza, sukun or shadda follows it in the same word."),
        ),
        (),
        ("Reported for every such letter, including the ones other rules extend.",),
    ),
    "madd_badal": (
        "madd",
        "مد البدل",
        "A",
        ("p.15",),
        "A madd letter that replaces the second of two hamzas takes the same two harakat as the "
        "natural madd; it follows a hamza in the same word.",
        (("after_hamza", "The madd letter comes right after a hamza in the same word."),),
        (),
        ("Also reported when the corpus writes a hamza with a maddah and no alef.",),
    ),
    "madd_iwad": (
        "madd",
        "مد العوض",
        "A",
        ("p.15", "p.16"),
        "When a word that ends in tanween with a fatha is stopped on, the tanween is replaced by "
        "an alef of two harakat. A tanween on the feminine ta (ة) is stopped on with a ha instead.",
        (
            ("stop", "The reading stops on the word."),
            ("fathatan", "The last letter carries a tanween fatha."),
        ),
        (("ta_marbuta", "A tanween on ة is not replaced by an alef."),),
        ("Waqf only: nothing is reported while the reading continues.",),
    ),
    "madd_harf_hay_tahar": (
        "madd",
        "الألف في هجاء أحرف حي طهر",
        "A",
        ("p.17",),
        "In the isolated letters ح ي ط ه ر at the opening of a surah the spelled-out name has an "
        "alef that lengthens by two harakat only.",
        (("opening", "The letter is one of ح ي ط ه ر at the opening of a surah."),),
        (),
        ("Openings are located by the verse-1 position of the 29 surahs that start with letters.",),
    ),
    "madd_sila_sughra_ha": (
        "madd",
        "الصلة الصغرى في هاء الضمير",
        "A",
        ("p.17", "p.18", "p.19"),
        "A pronoun ha between two vowelled letters is lengthened with a waw or yeh of two harakat "
        "when no hamza follows.",
        (
            ("between_vowelled", "The ha is the pronoun ha and sits between two moving letters."),
            ("no_hamza", "The next word does not begin with a hamza."),
        ),
        (
            (
                "seven_words",
                "Seven words are listed on p.19 as read with a kasra and no lengthening; the "
                "last, فألقه, is stated both ways by the book (see limitations). The corpus "
                "already omits the mark in the others.",
            ),
        ),
        (
            "The corpus marks the lengthening itself, so this follows that mark; dropped at a stop.",
            "Book A p.19 item 7 reads فألقه with kasra and sila, while p.20 reads it with kasra "
            "and no sila. The rule `madd_sila_ha_exception` lists both readings and chooses none.",
        ),
    ),
    "madd_sila_sughra_meem": (
        "madd",
        "الصلة الصغرى في ميم الجمع",
        "A",
        ("p.17", "p.18"),
        "A plural pronoun meem followed by a moving letter that is not a hamza may be read as in "
        "Hafs with a sukun, or joined with a waw of two harakat.",
        (
            ("plural_meem", "A final sakin meem of the plural pronoun (hum, kum, tum)."),
            ("no_hamza", "The next word does not begin with a hamza or with hamzat al-wasl."),
        ),
        (),
        (
            "Both readings are listed in `variants`; the meem carries no sign in the corpus.",
            "Before ba and meem the corpus writes the sakin meem with no sukun (as for ikhfa and "
            "idgham shafawi). Those places are included: p.17 says the sila applies to a plural "
            "meem before any moving letter that is not a hamza, and p.18 gives an example before a "
            "meem (في قلوبهم مرض); no example is given before a ba, so that case rests on the "
            'general wording. Their `variants` are the same as the older places, ["iskan", '
            '"sila_2_harakat"]: p.17 says the sila of the plural meem is « قدر حركتين ».',
            "The book does not say how the sila relates to ikhfa or idgham shafawi. By the "
            "construction of the rule, with the sila the meem is no longer sakin, so ikhfa/idgham "
            "shafawi on the same meem apply to the iskan reading only. This is an inference "
            "recorded in the notes of both annotations, not a statement of the book.",
        ),
    ),
    "madd_muttasil": (
        "madd",
        "المد الواجب المتصل",
        "A",
        ("p.19",),
        "A madd letter followed by a hamza in the same word is lengthened by three or four "
        "harakat, and that length is obligatory.",
        (("same_word", "The madd letter and the hamza are in the same word."),),
        (),
        ("The permitted lengths are listed in `variants`.",),
    ),
    "madd_munfasil": (
        "madd",
        "المد الجائز المنفصل",
        "A",
        ("p.19",),
        "A madd letter ending a word, followed by a hamza that begins the next word, is "
        "lengthened by two, three or four harakat.",
        (("split", "The madd letter ends a word and the next word begins with a hamza."),),
        (),
        ("Needs the next word: unresolved in `wasl` mode at the end of the last ayah.",),
    ),
    "madd_sila_kubra_ha": (
        "madd",
        "الصلة الكبرى في هاء الضمير",
        "A",
        ("p.19", "p.20"),
        "A pronoun ha before a hamza that begins the next word is lengthened with a waw or yeh "
        "measured like the separated madd.",
        (("hamza_next", "The ha is a pronoun ha and the next word begins with a hamza."),),
        (
            (
                "two_words",
                "يؤده إليك is read with a kasra and no lengthening; فألقه إليهم is stated both "
                "ways by the book (see limitations).",
            ),
        ),
        (
            "Follows the sign the corpus writes on the ha.",
            "فألقه: p.20 gives kasra without the sila, but p.19 item 7 gives kasra with the sila. "
            "The two pages disagree; `madd_sila_ha_exception` keeps both readings in `variants`.",
        ),
    ),
    "madd_sila_kubra_meem": (
        "madd",
        "الصلة الكبرى في ميم الجمع",
        "A",
        ("p.19", "p.20"),
        "A plural pronoun meem before a hamza that begins the next word may be read with a sukun "
        "or joined with a waw measured like the separated madd.",
        (("plural_meem", "A final sakin plural-pronoun meem followed by a hamza."),),
        (),
        ("The permitted lengths are listed in `variants`.",),
    ),
    "madd_arid_sukun": (
        "madd",
        "المد العارض للسكون",
        "B",
        ("p.20",),
        "A madd letter just before the last letter of a word that is stopped on may be lengthened "
        "by two, four or six harakat.",
        (
            ("stop", "The reading stops on the word."),
            ("penultimate", "The madd letter is right before the last letter."),
        ),
        (),
        ("Waqf only.",),
    ),
    "madd_muttasil_arid": (
        "madd",
        "المد المتصل العارض",
        "B",
        ("p.20",),
        "A connected madd whose hamza is the last letter of a word that is stopped on is stopped "
        "with three, four or six harakat, never shortened to two.",
        (
            ("stop", "The reading stops on the word."),
            ("hamza_last", "The hamza is the last letter of the word."),
        ),
        (),
        ("Waqf only.",),
    ),
    "madd_lin": (
        "madd",
        "مد اللين",
        "B",
        ("p.21",),
        "A sakin waw or yeh after a fatha, right before the last letter of a stopped word, may be "
        "lengthened by two, four or six harakat.",
        (
            ("stop", "The reading stops on the word."),
            ("lin_letter", "A sakin waw or yeh after a fatha sits before the last letter."),
        ),
        (),
        ("Waqf only.",),
    ),
    "madd_lazim_kalimi_muthaqqal": (
        "madd",
        "المد اللازم الكلمي المثقل",
        "A",
        ("p.21",),
        "A madd letter followed by a shadda in the same word is lengthened by six harakat.",
        (("shadda", "The madd letter is followed by a doubled letter in the same word."),),
        (),
        ("Only a maddah-marked alef is taken as the madd letter, to avoid the wasl alef.",),
    ),
    "madd_lazim_kalimi_mukhaffaf": (
        "madd",
        "المد اللازم الكلمي المخفف",
        "C",
        ("p.21", "p.22"),
        "A madd letter followed by an original sukun in the same word is lengthened by six harakat; "
        "the Qur'an has this in محياي and in آلآن.",
        (("sukun", "The madd letter is followed by an original sukun in the same word."),),
        (),
        (
            "A closed list: the sukun case and the word spelled آلآن are both reported.",
            "آلآن (Yunus 51 and 91): Book A p.21 gives three readings, a madd of six harakat "
            "taken from the origin, a madd of two harakat taken from the accidental cause, and a "
            "softening of the wasl hamza with no madd. They are listed in `variants`; none is chosen.",
        ),
    ),
    "madd_lazim_harfi_muthaqqal": (
        "madd",
        "المد اللازم الحرفي المثقل",
        "A",
        ("p.22",),
        "In an isolated letter whose last sound is assimilated into the next letter (the lam of "
        "الم and the sin of طسم) the madd is six harakat.",
        (("assimilated", "An isolated letter from نقص عسلكم is merged into the next letter."),),
        (),
        ("Openings are located by the verse-1 position of the 29 surahs that start with letters.",),
    ),
    "madd_lazim_harfi_mukhaffaf": (
        "madd",
        "المد اللازم الحرفي المخفف",
        "A",
        ("p.22", "p.23"),
        "An isolated letter from نقص عسلكم that is not merged into the next one is lengthened by "
        "six harakat; for the ع of كهيعص and حم عسق two readings (four or six) are given.",
        (("letter", "An isolated letter from نقص عسلكم at the opening of a surah."),),
        (),
        ("The permitted lengths for ع are listed in `variants`.",),
    ),
    "madd_letter_dropped": (
        "madd",
        "حذف حرف المد لالتقاء الساكنين",
        "B",
        ("p.24",),
        "A word-final madd letter is not pronounced when the next word begins with hamzat al-wasl "
        "and a sakin letter, because two sakin sounds would meet.",
        (
            ("joined", "The reading continues into the next word."),
            ("wasl_next", "The next word begins with hamzat al-wasl and a sakin letter."),
        ),
        (),
        ("Wasl only; at a stop nothing is dropped.",),
    ),
    "hamza_ibdal_yajuj": (
        "hamza",
        "إبدال الهمزة ألفا في يأجوج ومأجوج",
        "C",
        ("p.25",),
        "The hamza of يأجوج and مأجوج is replaced by an alef.",
        (("words", "The words are يأجوج and مأجوج (18:94 and 21:96 in the Kufian count)."),),
        (),
        ("A word list; the corpus already spells the replacement.",),
    ),
    "hamza_ibdal_ruya": (
        "hamza",
        "إبدال الهمزة في رئيا",
        "C",
        ("p.25",),
        "The hamza of رئيا (Maryam 19:74) is replaced by a yeh that is merged into the next yeh.",
        (("word", "The word is رئيا in Maryam 74."),),
        (),
        ("A one-word list.",),
    ),
    "hamza_ibdal_minsaa": (
        "hamza",
        "إبدال الهمزة في منسأته",
        "C",
        ("p.25",),
        "The hamza of منسأته (Saba 34:14) is replaced by an alef.",
        (("word", "The word is منسأته in Saba 14."),),
        (),
        ("A one-word list.",),
    ),
    "hamza_ibdal_saala": (
        "hamza",
        "إبدال الهمزة في سأل",
        "C",
        ("p.25",),
        "The hamza of سأل (al-Ma'arij 70:1) is replaced by an alef.",
        (("word", "The word is سأل in al-Ma'arij 1."),),
        (),
        ("A one-word list.",),
    ),
    "hamza_ibdal_musada": (
        "hamza",
        "إبدال الهمزة في مؤصدة",
        "C",
        ("p.25",),
        "The hamza of مؤصدة (al-Balad 20, al-Humaza 8) is replaced by a waw.",
        (("word", "The word is مؤصدة in the two named places."),),
        (),
        ("A closed list.",),
    ),
    "hamza_waw_huzu_kufu": (
        "hamza",
        "همز الواو في هزوا وكفوا",
        "C",
        ("p.25",),
        "The waw of هزوا (wherever it occurs) and of كفوا (al-Ikhlas 4) is read as a hamza.",
        (("words", "The words are هزوا and كفوا."),),
        (),
        ("Matched on the corpus spelling with a hamza; every occurrence is reported.",),
    ),
    "hamza_nabi": (
        "hamza",
        "همز النبي ونحوها",
        "C",
        ("p.25", "p.26"),
        "The word for prophet and its derivatives are read with a hamza (النبيء, نبيئا, "
        "الأنبياء read as أنبئاء...) wherever they occur.",
        (("noun", "The word is the noun for prophet; a verb with a shadda on the ba is not it."),),
        (
            (
                "two_places",
                "In the two places al-Ahzab 50 and 53 the word is read without hamza "
                "when joined to the next word.",
            ),
        ),
        ("Matched on the corpus spelling that carries a hamza.",),
    ),
    "hamza_nabi_exception": (
        "hamza",
        "استثناء النبي في موضعي الأحزاب",
        "C",
        ("p.26",),
        "In al-Ahzab 50 and 53 the word for prophet is read without hamza when joined to the next "
        "word, and with hamza if the reading stops on it.",
        (("places", "The two places are للنبيء إن (33:50) and النبيء إلا (33:53)."),),
        (),
        ("The two places are given in the Kufian numbering used by the book.",),
    ),
    "hamza_double_in_word": (
        "hamza",
        "الهمزتان في كلمة",
        "A",
        ("p.26",),
        "When two hamzas meet in one word and the first is fatha, an alef is placed between them "
        "and the second hamza is softened between hamza and the letter of its vowel.",
        (("two_hamzas", "Two hamzas follow each other in one word, the first with a fatha."),),
        (("aimma", "In أئمة no alef is placed between them; only the second is softened."),),
        ("The corpus already writes the added alef, which the note records.",),
    ),
    "hamza_double_exception": (
        "hamza",
        "استثناءات الهمزتين في كلمة",
        "C",
        ("p.26", "p.27"),
        "The word أئمة has no alef between its hamzas, and أشهدوا (az-Zukhruf 19) may be read with "
        "or without the alef between them.",
        (("words", "The words are أئمة and أشهدوا in az-Zukhruf 19."),),
        (),
        (
            "Other exceptions of the same page (the added interrogative hamza in ءامنتم and "
            "ءأله) are not matched.",
        ),
    ),
    "hamza_two_words_same": (
        "hamza",
        "الهمزتان المتفقتان في كلمتين",
        "C",
        ("p.27", "p.28"),
        "A final hamza meeting an initial hamza with the same vowel: for two fathas the first is "
        "dropped (short or medium length); for two dammas or two kasras the first is softened.",
        (("two_words", "A final hamza and the next word's initial hamza share one vowel."),),
        (),
        ("Not detected: the Qaloun text already carries the result and not the original hamza.",),
    ),
    "hamza_two_words_different": (
        "hamza",
        "الهمزتان المختلفتان في كلمتين",
        "C",
        ("p.28", "p.29"),
        "A final hamza meeting a differently-vowelled initial hamza: the second is softened or "
        "replaced by a letter according to the five cases the book lists.",
        (("two_words", "A final hamza and the next word's initial hamza have different vowels."),),
        (),
        ("Not detected: the Qaloun text already carries the result and not the original hamza.",),
    ),
    "hamzat_wasl_article": (
        "hamza",
        "همزة الوصل في أل التعريف",
        "A",
        ("p.29",),
        "Hamzat al-wasl in the article is pronounced with a fatha when the reading starts there "
        "and dropped when joined.",
        (("article", "The word begins with the article alef-lam."),),
        (),
        ("Located by the wasl mark the corpus writes on the alef.",),
    ),
    "hamzat_wasl_noun": (
        "hamza",
        "همزة الوصل في الأسماء",
        "C",
        ("p.29", "p.30"),
        "Hamzat al-wasl occurs in seven nouns: اسم، ابن، ابنة، امرؤ، امرأة، اثنان/اثنين، "
        "اثنتان/اثنتين; the reading starts on it with a kasra.",
        (("nouns", "The word is one of the seven nouns."),),
        (),
        ("Located by the second wasl mark the corpus writes on the alef.",),
    ),
    "hamzat_wasl_verb": (
        "hamza",
        "همزة الوصل في الأفعال",
        "B",
        ("p.30",),
        "Hamzat al-wasl begins the imperative of three-letter verbs and the past tense, imperative "
        "and verbal noun of five- and six-letter verbs; the reading starts on it with a damma if "
        "the third letter has a damma, otherwise a kasra.",
        (
            (
                "verb",
                "The word begins with a wasl alef that is neither the article nor a listed noun.",
            ),
        ),
        (("four_verbs", "امشوا، ابنوا، امضوا، اقضوا are begun with a kasra."),),
        ("Verb status is assumed from the spelling; no morphology is used.",),
    ),
    "sakin_before_hamzat_wasl": (
        "hamza",
        "تحريك الساكن قبل همزة الوصل",
        "B",
        ("p.31",),
        "A sakin letter before hamzat al-wasl takes a vowel: the noon of من takes a fatha, a "
        "plural meem takes a damma, and other sakin letters take the vowel the wasl hamza begins "
        "with.",
        (("before_wasl", "The next word begins with hamzat al-wasl."),),
        (),
        ("Only min, the plural meem and tanween are recognised; other sakin letters are not.",),
    ),
    "ra_tafkhim": (
        "tafkhim",
        "تفخيم الراء",
        "B",
        ("p.33",),
        "A ra that is not word-final is heavy when it has a fatha or damma, or is sakin after a "
        "fatha, a damma, an accidental kasra, or an original kasra followed by a non-kasra "
        "isti'la letter.",
        (("not_final", "The ra is not the last letter of a stopped word."),),
        (),
        (
            "The five words قرطاس، فرصادا، إرصادا، مرصادا، المرصاد are covered by the isti'la clause.",
        ),
    ),
    "ra_tarqiq": (
        "tafkhim",
        "ترقيق الراء",
        "B",
        ("p.33", "p.34"),
        "A ra that is not word-final is light when it has a kasra, or is sakin after an original "
        "kasra with no isti'la letter after it.",
        (("not_final", "The ra is not the last letter of a stopped word."),),
        (),
        (),
    ),
    "ra_jawaz": (
        "tafkhim",
        "جواز الوجهين في راء فرق",
        "C",
        ("p.34",),
        "In فرق (ash-Shu'ara 63) the sakin ra after a kasra before a kasra qaf may be read heavy "
        "or light.",
        (("word", "The word is فرق."),),
        (),
        ("A one-word list.",),
    ),
    "ra_mutatarrif_tafkhim": (
        "tafkhim",
        "تفخيم الراء المتطرفة",
        "B",
        ("p.34",),
        "A ra at the end of a word that is stopped on is heavy when sakin after a fatha, an alef, "
        "a damma or a waw.",
        (("stop", "The reading stops on the word."),),
        (),
        ("Waqf only.",),
    ),
    "ra_mutatarrif_tarqiq": (
        "tafkhim",
        "ترقيق الراء المتطرفة",
        "B",
        ("p.34",),
        "A ra at the end of a word that is stopped on is light when sakin after a kasra or a "
        "sakin yeh.",
        (("stop", "The reading stops on the word."),),
        (),
        ("Waqf only.",),
    ),
    "ra_mutatarrif_jawaz": (
        "tafkhim",
        "جواز الوجهين في الراء المتطرفة",
        "C",
        ("p.34",),
        "At a stop, القطر and مصر, and ra after a dropped yeh in يسر and نذر, may be read heavy "
        "or light.",
        (("words", "The words are القطر، مصر، and يسر/نذر without their yeh."),),
        (),
        ("Waqf only.",),
    ),
    "lam_jalala_tafkhim": (
        "tafkhim",
        "تفخيم لام لفظ الجلالة",
        "B",
        ("p.34", "p.35"),
        "The lam of the name of Allah is heavy when the letter before it has a fatha or damma, "
        "or when the reading starts on it.",
        (("name", "The word is the name of Allah."),),
        (),
        ("A selection that starts on the name is taken as the start of a reading.",),
    ),
    "lam_jalala_tarqiq": (
        "tafkhim",
        "ترقيق لام لفظ الجلالة",
        "B",
        ("p.35",),
        "The lam of the name of Allah is light when the letter before it has a kasra, including "
        "a tanween that takes a kasra before it.",
        (("name", "The word is the name of Allah."),),
        (),
        (),
    ),
    "alef_tafkhim": (
        "tafkhim",
        "تفخيم الألف",
        "B",
        ("p.35",),
        "A madd alef is heavy after an isti'la letter (خ ص ض غ ط ق ظ) or after the heavy lam of "
        "the name of Allah.",
        (("after_heavy", "The letter before the alef is an isti'la letter or the heavy lam."),),
        (),
        ("The heavy lam of the name of Allah is taken from the same word only.",),
    ),
    "alef_tarqiq": (
        "tafkhim",
        "ترقيق الألف",
        "B",
        ("p.35",),
        "A madd alef is light after any other letter.",
        (("after_light", "The letter before the alef is not heavy."),),
        (),
        (),
    ),
    "ghunna_tafkhim": (
        "tafkhim",
        "تفخيم الغنة",
        "B",
        ("p.35",),
        "The ghunna is heavy when a noon or tanween is hidden before one of ص ض ط ظ ق.",
        (("ikhfa", "A noon or tanween meets one of the five heavy ikhfa letters."),),
        (),
        (),
    ),
    "ghunna_tarqiq": (
        "tafkhim",
        "ترقيق الغنة",
        "B",
        ("p.35",),
        "The ghunna is light for every other hidden noon or tanween.",
        (("ikhfa", "A noon or tanween meets one of the other ten ikhfa letters."),),
        (),
        (),
    ),
    "taqlil_tawrat": (
        "imala",
        "التقليل في التوراة",
        "C",
        ("p.35",),
        "Qaloun reads the alef of التوراة between alef and yeh (taqlil); the book gives the "
        "other reading as an opening like Hafs.",
        (("word", "The word is التوراة wherever it occurs."),),
        (),
        ("The second reading the book mentions is not listed in `variants`.",),
    ),
    "imala_har": (
        "imala",
        "الإمالة في هار",
        "C",
        ("p.35",),
        "Qaloun inclines the alef of هار (at-Tawba 109) toward yeh (imala).",
        (("word", "The word is هار in at-Tawba 109."),),
        (),
        ("A one-word list.",),
    ),
}


def build_rule(rule_id: str, spec: tuple) -> TajwidRule:
    family, name_ar, detectability, pages, definition, conditions, exceptions, limits = spec
    evidence = tuple(Citation(**BOOK_A, locator=page) for page in pages)

    def clause(kind: str, item: tuple[str, str]) -> RuleClause:
        return RuleClause(clause_id=item[0], kind=kind, description=item[1], evidence=evidence)

    return TajwidRule(
        rule_id=rule_id,
        version="1",
        name_ar=name_ar,
        definition=definition,
        riwaya="qaloun",
        tariq="unspecified",
        family=FAMILY_ID[family],
        detectability=detectability,
        legend_class_ids=(),
        limitations=COMMON_LIMITATIONS + tuple(limits),
        conditions=tuple(clause("condition", c) for c in conditions),
        exceptions=tuple(clause("exception", e) for e in exceptions),
        evidence=evidence,
        validation_status="unreviewed",
        validation_record_ids=(),
    )


def main() -> int:
    knowledge = ROOT / "knowledge" / "rules"
    for rule_id, spec in RULES.items():
        rule = build_rule(rule_id, spec)
        target = knowledge / rule_id / "1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(rule.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")
    print(f"{len(RULES)} Book A rule records written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
