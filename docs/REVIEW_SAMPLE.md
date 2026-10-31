# Reviewer worksheet

For the future qualified reviewer. Every row is a **candidate** from a deterministic
detector (waqf reading, one ayah at a time); none is verified. References only: read the
ayah with `get_qaloun_passage`, the rule with `get_tajwid_rule`, and the cited book pages
from your own copy. Codepoints are a half-open range into the unchanged ayah text;
the word index counts words that contain at least one letter. Mark each row correct,
wrong or doubtful and note a reason; a decision becomes a `ValidationRecord` only
under your name.

Open points for the reviewer, independent of the sample:

- Books A (pp.5-6) and B (p.58) classify the completeness of idgham with ghunna
  differently.
- Whether the corpus (tariq unspecified) follows the Abu Nashit path the rules cite.
- Lam rules cite book A only; the Abu Nashit book has not been read for them.
- Plural-mim connection (silat) and internal waqf signs are not modelled.

## `ghunna_mushaddad` (غنة النون والميم المشددتين)

7336 candidates in the corpus. Cited: p.11 (book-a), printed p.63 (pdf p.64) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:1 | 1 | 5-10 | 2 | geminated mim | |
| 6:3 | 6 | 36-39 | 111 | geminated mim | |
| 13:19 | 28 | 268-271 | 219-220 | geminated mim | |
| 26:186 | 5 | 26-29 | 336 | geminated mim | |
| 42:21 | 26 | 238-241 | 439 | geminated noon | |

## `idgham_bighunna` (الإدغام بغنة)

3923 candidates in the corpus. Cited: p.5 (book-a), p.6 (book-a), printed p.57 (pdf p.58) (book-b), printed p.58 (pdf p.59) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:4 | 3 | 23-25 | 3 | tanween; next word begins with one of the letters of ينمو | |
| 5:59 | 10 | 99-101 | 102 | tanween; next word begins with one of the letters of ينمو | |
| 12:77 | 19 | 140-143 | 213-214 | tanween; next word begins with one of the letters of ينمو | |
| 25:12 | 3 | 19-20 | 322 | noon sakina; next word begins with one of the letters of ينمو | |
| 42:9 | 11 | 108-110 | 437 | tanween; next word begins with one of the letters of ينمو | |

## `idgham_bilaghunna` (الإدغام بغير غنة)

1039 candidates in the corpus. Cited: p.5 (book-a), printed p.57 (pdf p.58) (book-b), printed p.58 (pdf p.59) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:1 | 7 | 53-55 | 2 | tanween; next word begins with lam or ra | |
| 5:50 | 36 | 341-342 | 100-101 | noon sakina; next word begins with lam or ra | |
| 12:2 | 4 | 39-41 | 205 | tanween; next word begins with lam or ra | |
| 22:71 | 22 | 202-204 | 303 | tanween; next word begins with lam or ra | |
| 41:5 | 15 | 141-143 | 431 | tanween; next word begins with lam or ra | |

## `idgham_shafawi` (الإدغام الشفوي)

832 candidates in the corpus. Cited: p.9 (book-a), printed p.62 (pdf p.63) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:9 | 2 | 13-14 | 3 | mim sakina before a moving mim | |
| 5:108 | 25 | 231-232 | 108-109 | mim sakina before a moving mim | |
| 12:40 | 9 | 84-85 | 209-210 | mim sakina before a moving mim | |
| 26:42 | 2 | 10-11 | 330 | mim sakina before a moving mim | |
| 39:52 | 7 | 58-59 | 420 | mim sakina before a moving mim | |

## `idhar_halqi` (الإظهار الحلقي)

3009 candidates in the corpus. Cited: p.4 (book-a), p.5 (book-a), printed p.56 (pdf p.57) (book-b), printed p.57 (pdf p.58) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 1:6 | 3 | 20-22 | 1 | noon sakina; next letter is a throat letter | |
| 5:68 | 21 | 197-199 | 103 | noon sakina; next letter is a throat letter | |
| 11:71 | 8 | 70-73 | 200 | tanween; next letter is a throat letter | |
| 24:21 | 24 | 244-246 | 314 | noon sakina; next letter is a throat letter | |
| 40:40 | 8 | 61-63 | 426 | noon sakina; next letter is a throat letter | |

## `idhar_mutlaq` (الإظهار المطلق)

125 candidates in the corpus. Cited: p.6 (book-a), printed p.58 (pdf p.59) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:84 | 38 | 385-387 | 12 | noon sakina; idgham letter in the same word | |
| 5:35 | 29 | 262-264 | 98 | noon sakina; idgham letter in the same word | |
| 10:64 | 5 | 46-48 | 187-188 | noon sakina; idgham letter in the same word | |
| 20:129 | 12 | 107-109 | 285 | noon sakina; idgham letter in the same word | |
| 37:97 | 4 | 28-30 | 406 | noon sakina; idgham letter in the same word | |

## `idhar_shafawi` (الإظهار الشفوي)

6155 candidates in the corpus. Cited: p.9 (book-a), p.10 (book-a), printed p.63 (pdf p.64) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 1:1 | 1 | 7-9 | 1 | mim sakina before another letter | |
| 5:35 | 26 | 241-243 | 98 | mim sakina before another letter | |
| 10:49 | 17 | 122-124 | 186 | mim sakina before another letter | |
| 23:74 | 2 | 21-23 | 309 | mim sakina before another letter | |
| 41:21 | 9 | 82-84 | 433 | mim sakina before another letter | |

## `ikhfa_haqiqi` (الإخفاء الحقيقي)

5307 candidates in the corpus. Cited: p.7 (book-a), p.8 (book-a), printed p.60 (pdf p.61) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:2 | 8 | 86-87 | 2 | noon sakina; next letter is one of the fifteen ikhfa letters | |
| 5:25 | 20 | 196-197 | 97 | noon sakina; next letter is one of the fifteen ikhfa letters | |
| 11:68 | 12 | 104-105 | 200 | noon sakina; next letter is one of the fifteen ikhfa letters | |
| 24:42 | 25 | 205-207 | 318 | tanween; next letter is one of the fifteen ikhfa letters | |
| 41:13 | 17 | 143-144 | 432 | noon sakina; next letter is one of the fifteen ikhfa letters | |

## `ikhfa_shafawi` (الإخفاء الشفوي)

496 candidates in the corpus. Cited: p.9 (book-a), printed p.62 (pdf p.63) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:7 | 10 | 86-87 | 3 | mim sakina before ba | |
| 5:107 | 16 | 159-160 | 108 | mim sakina before ba | |
| 10:13 | 9 | 89-90 | 182 | mim sakina before ba | |
| 23:60 | 2 | 12-13 | 308 | mim sakina before ba | |
| 40:22 | 5 | 48-49 | 424 | mim sakina before ba | |

## `iqlab` (الإقلاب)

283 candidates in the corpus. Cited: p.7 (book-a), printed p.59 (pdf p.60) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:26 | 5 | 40-42 | 5 | noon sakina; next letter is ba | |
| 4:36 | 19 | 216-218 | 72-73 | noon sakina; next letter is ba | |
| 10:14 | 6 | 49-51 | 182 | noon sakina; next letter is ba | |
| 22:26 | 13 | 115-117 | 298 | noon sakina; next letter is ba | |
| 40:4 | 6 | 51-53 | 422-423 | noon sakina; next letter is ba | |

## `lam_qamariya` (اللام القمرية)

5370 candidates in the corpus. Cited: p.13 (book-a).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 1:1 | 1 | 3-5 | 1 | article lam pronounced before its letter | |
| 5:97 | 26 | 219-221 | 107 | article lam pronounced before its letter | |
| 13:32 | 10 | 75-77 | 221 | article lam pronounced before its letter | |
| 28:20 | 9 | 69-71 | 349 | article lam pronounced before its letter | |
| 43:74 | 2 | 9-11 | 447 | article lam pronounced before its letter | |

## `lam_shamsiya` (اللام الشمسية)

4042 candidates in the corpus. Cited: p.12 (book-a), p.13 (book-a).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 1:2 | 1 | 3-4 | 1 | article lam assimilated into its letter | |
| 5:55 | 2 | 11-12 | 101 | article lam assimilated into its letter | |
| 12:107 | 10 | 86-87 | 216 | article lam assimilated into its letter | |
| 25:60 | 8 | 66-67 | 326 | article lam assimilated into its letter | |
| 42:9 | 2 | 11-12 | 437 | article lam assimilated into its letter | |

## `qalqala_kubra` (القلقلة الكبرى)

912 candidates in the corpus. Cited: p.44 (book-a), printed p.52 (pdf p.53) (book-b), printed p.53 (pdf p.54) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:59 | 14 | 137-139 | 8-9 | sakin letter at the end of the word | |
| 7:70 | 2 | 8-10 | 139 | sakin letter at the end of the word | |
| 16:113 | 1 | 6-8 | 245 | sakin letter at the end of the word | |
| 35:35 | 14 | 112-115 | 395 | final letter at a stop, without shadda | |
| 50:12 | 7 | 64-66 | 471 | final letter at a stop, without shadda | |

## `qalqala_sughra` (القلقلة الصغرى)

2933 candidates in the corpus. Cited: p.44 (book-a), printed p.52 (pdf p.53) (book-b), printed p.53 (pdf p.54) (book-b).

| ayah | word | codepoints | app page | note | verdict |
| --- | ---: | --- | --- | --- | --- |
| 2:2 | 7 | 74-76 | 2 | sakin mid-word | |
| 6:70 | 34 | 287-289 | 118-119 | sakin mid-word | |
| 15:67 | 4 | 34-36 | 232 | sakin mid-word | |
| 26:183 | 2 | 8-10 | 336 | sakin mid-word | |
| 43:74 | 2 | 13-15 | 447 | sakin mid-word | |

