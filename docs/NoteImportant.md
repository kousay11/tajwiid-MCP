# Notes importantes

Ce fichier garde ce qu'il faut savoir avant de tester ou d'utiliser le MCP : le problème
rencontré dans l'Inspector, d'où viennent les données, et l'analyse des résultats déjà testés.
À compléter après chaque nouveau test (voir la fin).

## 1. Problème rencontré avec l'Inspector, et sa solution

**Symptôme.** `health_check` répondait, mais les autres tools (par exemple `analyze_app_page`)
renvoyaient :

```json
{"status": "error", "error": {"code": "DATA_UNAVAILABLE",
 "message": "Public Quran source root is not configured"}}
```

`health_check` montrait aussi `"quran_data": "not_configured"`.

**Cause.** Le serveur lit le texte du Quran dans un dépôt externe (Wirdi AI) dont le chemin est
donné par la variable `WIRDI_AI_ROOT`. Lancée avant `npx` (`WIRDI_AI_ROOT=... npx inspector ...`),
la variable n'arrivait pas jusqu'au serveur : l'Inspector démarre le serveur lui-même avec un
environnement filtré. Sans la variable, tout tool qui lit le Quran échoue de façon contrôlée.
`health_check` ne lit aucune donnée, donc il marchait.

**Solution.** Passer la variable à l'Inspector :

```bash
cd /home/najjar/Documents/Me/wirdi-mcp
npx @modelcontextprotocol/inspector -e WIRDI_AI_ROOT=/home/najjar/Documents/Me/wirdi-Ai .venv/bin/wirdi-mcp
```

ou la saisir dans « Environment Variables » de l'interface, puis Disconnect / Connect. Contrôle :
`health_check` doit afficher `"quran_data": "configured_unchecked"`.

**Deuxième cause, dans la requête.** Le formulaire proposait `following: {"riwaya": "qaloun"}`,
qui est une référence incomplète. Il faut `null` (ou une référence complète de l'ayah suivante),
plus `page` et `reading_context.mode`. La requête qui marche :

```json
{"page": 263,
 "reading_context": {"mode": "waqf", "basis": "requested", "preceding": null,
                     "following": null, "stop_after_word": null},
 "rule_ids": [], "families": [], "limit": 100, "offset": 0}
```

## 2. D'où viennent les données

| Donnée | Origine | Garde-fous |
| --- | --- | --- |
| Texte du Quran (Qaloun) | Fichiers publics du dépôt Wirdi AI, lus en lecture seule via `WIRDI_AI_ROOT`. Le jeu est « KFGQPC Qaloun via Qur'anpedia » (distribution `risan/quran-json`, commit `6523a9ad3b73bb7e8cb3a9cdf0ea774b8bab3123`), soit 6 214 ayat | Empreinte SHA-256 du corpus vérifiée à chaque appel (`ece0a2b0…d1303`) ; le texte n'est jamais modifié ni recopié |
| Pagination 559 pages | Fichier de pagination du même dépôt | Empreinte vérifiée (`ca7aa4e4…ccfc0`) ; page 263 = « verified_against_edition » |
| Numérotation | Compte Qaloun du corpus. Le lien vers la numérotation kufienne (celle que cite le livre A) est `number_in_hafs` | Les listes du livre A sont comparées aux numéros kufiens |
| Règles de tajwid | Paraphrases rédigées pour ce projet, dans `knowledge/rules/` ; sources : livre A (51 p.) pour les 81 règles, livre B (Abu Nashit) pour 12 des 14 premières | Empreinte de chaque fiche vérifiée ; chaque citation donne livre et page |
| Détection | Code déterministe local (aucun LLM, aucun RAG, aucun réseau) | Chaque résultat est `candidate`, jamais vérifié |

Le texte vient du Wirdi AI, jamais d'un PDF. Les PDF (livres A, B et mushaf) servent seulement à
rédiger les fiches ; ils ne sont pas dans git. Le corpus identifie Qaloun mais n'atteste pas Abu
Nashit : `tariq` reste `unspecified`.

## 3. Analyse du résultat testé : `analyze_app_page`, page 263, waqf, toutes familles

**Ce que dit la réponse.**

- `status: ok`, `pagination_status: verified_against_edition`.
- La page porte le début de 10 ayat : Kahf 18:39 à 18:48 (le 48 continue page 264). L'ayah 18:38
  commence page 262 et finit page 263 ; il est listé à part (`continued_from_previous_page`) et
  non analysé deux fois.
- `total: 280` candidats, 100 renvoyés (`limit: 100`), `next_offset: 100` : relancer avec
  `offset: 100` puis `200` pour voir les 180 autres. Les 100 premiers vont de 18:39 à 18:44.
- `coverage: complete_for_requested_rules`, `unresolved: {}` : aucune position n'a manqué de contexte.
- `skipped` : 10 tanwins à l'arrêt (aucune règle de noon ne s'y applique), 2 lafz al-jalala
  (famille traitée par `lam_jalala_*`), 1 noon nu devant alef.
- 77 règles évaluées (à la date de ce test ; il y en a 79 aujourd'hui). Tous les statuts sont `candidate`, `validation_status: unreviewed`.

**Comptes par règle sur les 280 candidats** (`rule_counts`) :

| Famille | Règles (nombre) |
| --- | --- |
| Madd | `madd_tabii` 75, `madd_iwad` 10, `madd_muttasil` 6, `madd_sila_sughra_ha` 5, `madd_sila_kubra_meem` 3, `madd_munfasil` 2, `madd_sila_sughra_meem` 1, `madd_letter_dropped` 1 |
| Heavy / light | `alef_tarqiq` 32, `alef_tafkhim` 3, `ra_tafkhim` 19, `ra_tarqiq` 8, `lam_jalala_tafkhim` 1, `lam_jalala_tarqiq` 2, `ghunna_tarqiq` 11, `ghunna_tafkhim` 1 |
| Noon / mim / lam | `ikhfa_haqiqi` 12, `idgham_bighunna` 11, `idhar_shafawi` 8, `idhar_halqi` 7, `idgham_bilaghunna` 2, `idgham_shafawi` 2, `idhar_mutlaq` 2, `ghunna_mushaddad` 8, `lam_qamariya` 13, `lam_shamsiya` 6, `qalqala_sughra` 4, `qalqala_kubra` 2 |
| Hamza / ya | `hamzat_wasl_article` 19, `sakin_before_hamzat_wasl` 2, `ya_idafa_fath` 2 |

**Contrôles de cohérence qui passent.**

- `ghunna_tarqiq` (11) + `ghunna_tafkhim` (1) = `ikhfa_haqiqi` (12) : chaque ikhfa reçoit une qualité de ghunna et une seule.
- `alef_tarqiq` (32) + `alef_tafkhim` (3) = 35 alefs de madd ; `madd_tabii` (75) est plus large parce qu'il couvre aussi les waw et ya de madd.
- `madd_iwad` (10) tombe sur les mots à tanwin fatha en fin d'ayah, donc sur des fins d'ayah arrêtées en waqf.
- Chaque annotation porte son ancre (`start_codepoint`, `end_codepoint`, empreinte de l'ayah), la page de l'application (263) et les pages du livre cité.
- `variants` n'est rempli que là où le livre admet plusieurs lectures : `madd_muttasil` (3 ou 4 harakat) et `madd_munfasil` (2, 3 ou 4). Le moteur n'en choisit aucune.

**Ce qui est normal mais peut surprendre.**

- Une même lettre porte plusieurs annotations quand elle relève de plusieurs règles (par exemple un alef de madd : `madd_tabii` ou `madd_muttasil`, plus `alef_tarqiq`). Ce sont des règles différentes, pas des doublons.
- Le même noon porte `ikhfa_haqiqi` et `ghunna_tarqiq` ou `ghunna_tafkhim` : deux niveaux de la même règle.
- `alef_tarqiq` et `alef_tafkhim` ont `note: null` : ils n'ont rien d'autre à dire.
- La majorité des résultats est du madd naturel et de l'article : ce sont les règles les plus fréquentes du texte.

**Ce que je recommande de relire à la main** (je n'ai pas relu ces ayat contre le livre) :

1. Les 2 `ya_idafa_fath` (vus à 18:39 et 18:41) : vérifier qu'il s'agit bien d'un ya de la première personne ouvert devant une hamza.
2. Les 2 `sakin_before_hamzat_wasl` (le premier est à 18:39) et le `madd_letter_dropped` : vérifier la voyelle donnée à la lettre sakin et la chute de la lettre de madd devant همزة الوصل.
3. Les 2 `lam_jalala_tarqiq` et le `lam_jalala_tafkhim` : vérifier la voyelle qui précède le nom d'Allah.
4. Les 3 `madd_sila_kubra_meem` : la mim du pluriel devant une hamza admet l'iskan ou la silat ; le moteur liste les deux lectures dans `variants` et ne choisit pas.
5. Les 280 candidats sont tous non vérifiés : aucun relecteur qualifié n'a confirmé une seule annotation.

## 4. Autres points à retenir

- `get_tajwid_explanation` renvoie toujours `UNSUPPORTED_CAPABILITY` tant qu'aucun relecteur n'a validé d'annotation.
- `get_source_page` et `search_source_pages` ne marchent que si le magasin de pages local du livre a été construit sur la machine (`scripts/build_page_store.py`) ; sinon `DATA_UNAVAILABLE`.
- En `wasl`, la dernière position de la sélection dépend de l'ayah suivante : sans `following`, elle est dans `unresolved`.
- Ce que le MCP ne détecte pas est listé dans [BOOK_A_COVERAGE](BOOK_A_COVERAGE.md).
- Requêtes prêtes à copier pour chaque famille : [TESTING_GUIDE](TESTING_GUIDE.md).

## 5. Journal des tests (à compléter)

| Date | Tool et requête | Résultat | Remarque |
| --- | --- | --- | --- |
| 2026-10-31 | `health_check` (Inspector, sans variable) | `quran_data: not_configured` | `WIRDI_AI_ROOT` non transmise |
| 2026-10-31 | `analyze_app_page` page 263, waqf, sans variable | `DATA_UNAVAILABLE` | même cause |
| 2026-10-31 | `analyze_app_page` page 263, waqf, toutes familles, avec variable | `ok`, 280 candidats (100 renvoyés) | analysé au point 3 |

Pour chaque nouveau test : ajouter une ligne ci-dessus, puis, si le résultat est instructif, une
courte analyse (comptes, contrôles de cohérence, points à relire) dans le même style que le point 3.
