# Exemples de requêtes, un par outil

Chaque bloc JSON est le contenu **complet** de `arguments`, accolades extérieures comprises : colle-le tel quel dans l'éditeur de l'Inspector (« Edit as JSON »), puis **Execute Tool**. Ne colle pas seulement `selection`.

Chaque requête a été exécutée contre le serveur au moment de la génération du fichier (`scripts/build_examples_md.py`). Les numéros d'ayah sont ceux du compte Qaloun (6 214 ayat) : un numéro hors limites, comme 2:286, renvoie `INVALID_REFERENCE`.

## `health_check`

**Rôle.** État du serveur (aucun argument).

**Exemple.** Readiness. `quran_data` is `configured_unchecked` and `quran_source` is `bundled` by default.

```json
{}
```

**Résultat attendu.** `status: 'foundation_ready'`.

## `get_qaloun_passage`

**Rôle.** Texte Qaloun inchangé d'un passage, avec SHA-256 et pages (sur 559).

**Exemple.** The unchanged text of Al-Baqara 2:5-7 (Qaloun count) with SHA-256 and the 559-page span.

```json
{
  "selection": {
    "start": {
      "corpus_id": "wirdi-ai:quranpedia:qalun",
      "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
      "numbering_system": "wirdi-ai:qalun-6214",
      "riwaya": "qaloun",
      "tariq": "unspecified",
      "surah": 2,
      "ayah": 5
    },
    "end_ayah": 7
  }
}
```

**Résultat attendu.** `status: 'ok'`.

## `resolve_source_mapping`

**Rôle.** Où tombe le passage dans la numérotation Kufi/Hafs.

**Exemple.** Where Qaloun 2:5-7 falls in the Kufian/Hafs count (expected 2:6-8, `verified_difference`).

```json
{
  "selection": {
    "start": {
      "corpus_id": "wirdi-ai:quranpedia:qalun",
      "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
      "numbering_system": "wirdi-ai:qalun-6214",
      "riwaya": "qaloun",
      "tariq": "unspecified",
      "surah": 2,
      "ayah": 5
    },
    "end_ayah": 7
  },
  "target_corpus_id": "wirdi-ai:quranpedia:hafs",
  "target_corpus_version": "sha256:0136b913aeb5a6a0389681f988215791ddd848c4347f7cf5e9d2574db7f1da49",
  "target_numbering_system": "wirdi-ai:qpc-hafs-6236"
}
```

**Résultat attendu.** `status: 'ok'`.

## `list_tajwid_rules`

**Rôle.** Liste des règles (filtre facultatif `family`).

**Exemple.** All 89 rules with family, detectability, tariq and `has_detector`.

```json
{}
```

**Résultat attendu.** `status: 'ok'`.

## `get_tajwid_rule`

**Rôle.** Une fiche de règle avec ses citations.

**Exemple.** One rule record: definition, conditions, exceptions, limitations, citations.

```json
{
  "rule_id": "madd_munfasil",
  "version": "1"
}
```

**Résultat attendu.** `status: 'ok'`.

## `analyze_qaloun_tajwid`

**Rôle.** Annotations candidates sur 1 à 100 ayat.

**Exemple.** Every madd candidate of 2:1-7 in waqf (family filter).

```json
{
  "selection": {
    "start": {
      "corpus_id": "wirdi-ai:quranpedia:qalun",
      "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
      "numbering_system": "wirdi-ai:qalun-6214",
      "riwaya": "qaloun",
      "tariq": "unspecified",
      "surah": 2,
      "ayah": 1
    },
    "end_ayah": 7
  },
  "reading_context": {
    "mode": "waqf",
    "basis": "requested",
    "preceding": null,
    "following": null,
    "stop_after_word": null
  },
  "rule_ids": [],
  "families": [
    "madd"
  ],
  "include_candidates": true,
  "limit": 50,
  "offset": 0
}
```

**Résultat attendu.** `status: 'ok'`.

## `summarize_tajwid`

**Rôle.** Comptes par règle et par ayah.

**Exemple.** Counts per rule and per ayah for 2:1-7, madd family (9 rules, 7 ayat).

```json
{
  "surah": 2,
  "start_ayah": 1,
  "end_ayah": 7,
  "reading_context": {
    "mode": "waqf",
    "basis": "requested",
    "preceding": null,
    "following": null,
    "stop_after_word": null
  },
  "rule_ids": [],
  "families": [
    "madd"
  ],
  "limit": 50,
  "offset": 0
}
```

**Résultat attendu.** `status: 'ok'`.

## `analyze_app_page`

**Rôle.** Annotations des ayat qui commencent sur une page (1 à 559).

**Exemple.** Candidates for the ayat that begin on page 263 of the 559-page layout (Kahf 18:39-48).

```json
{
  "page": 263,
  "reading_context": {
    "mode": "waqf",
    "basis": "requested",
    "preceding": null,
    "following": null,
    "stop_after_word": null
  },
  "rule_ids": [],
  "families": [
    "madd"
  ],
  "limit": 50,
  "offset": 0
}
```

**Résultat attendu.** `status: 'ok'`.

## `list_reading_combinations`

**Rôle.** Lectures permises ensemble dans un ayah.

**Exemple.** Al Imran 3:38: a connected madd, then a connected madd made 'arid by the stop with a kasra. The book lists exactly 6 readings (Nabhan p.103); `basis` is `book_listed`.

```json
{
  "selection": {
    "start": {
      "corpus_id": "wirdi-ai:quranpedia:qalun",
      "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
      "numbering_system": "wirdi-ai:qalun-6214",
      "riwaya": "qaloun",
      "tariq": "unspecified",
      "surah": 3,
      "ayah": 38
    },
    "end_ayah": 38
  },
  "reading_context": {
    "mode": "waqf",
    "basis": "requested",
    "preceding": null,
    "following": null,
    "stop_after_word": null
  },
  "max_combinations": 200
}
```

**Résultat attendu.** `status: 'ok'`.

## `get_letter_properties`

**Rôle.** Makhraj et caractéristiques d'une lettre.

**Exemple.** Place of articulation and characteristics (Book A pp.40-45). One base letter per entry.

```json
{
  "letters": [
    "ق",
    "ء",
    "ر",
    "ا",
    "و",
    "ي"
  ]
}
```

**Résultat attendu.** `status: 'ok'`.

## `get_source_page`

**Rôle.** Texte d'une page d'un livre local (magasin de pages requis).

**Exemple.** Raw text of printed page 19 of Book A (madd muttasil, munfasil, sila kubra). Needs the local page store.

```json
{
  "edition_id": "book-a-2010",
  "page_start": 19,
  "page_end": 19
}
```

**Résultat attendu.** `status: 'ok'`. Il faut d'abord construire le magasin de pages local (`scripts/build_page_store.py`), sinon la réponse est `DATA_UNAVAILABLE`.

## `search_source_pages`

**Rôle.** Recherche d'un mot dans les pages locales (magasin de pages requis).

**Exemple.** Which pages of Book A contain « الصلة »: 15, 17, 18, 19, 20. Needs the local page store.

```json
{
  "query": "الصلة",
  "edition_ids": [
    "book-a-2010"
  ],
  "limit": 20
}
```

**Résultat attendu.** `status: 'ok'`. Il faut d'abord construire le magasin de pages local (`scripts/build_page_store.py`), sinon la réponse est `DATA_UNAVAILABLE`.

## Cas d'erreur utiles

Les requêtes d'erreur (`INVALID_REFERENCE`, `NOT_FOUND`, `UNSUPPORTED_VERSION`…) sont dans `docs/APPLY.json`, avec le code attendu dans `expect`.
