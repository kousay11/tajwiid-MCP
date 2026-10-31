from wirdi_mcp.tajwid.text import tokenize


def test_offsets_resolve_back_to_the_unchanged_text():
    text = "مِنْ هَادٍۖ ۞ وَالشَّمْسِ"
    words = tokenize(text)
    assert [w.index for w in words] == [1, 2, 3]  # the sign-only token is not a word
    for word in words:
        assert text[word.start : word.end].startswith(word.letters[0].char)
        for letter in word.letters:
            assert text[letter.start] == letter.char or text[letter.start] == "\u0640"
            assert text[letter.start : letter.end] == letter.char + letter.marks


def test_marks_attach_to_the_preceding_letter_and_never_change_the_text():
    word = tokenize("مِنْ")[0]
    assert [(x.char, x.marks) for x in word.letters] == [("م", "ِ"), ("ن", "ْ")]
    assert word.letters[1].has_sukun and not word.letters[1].is_bare


def test_bare_letter_has_no_vowel_sukun_shadda_or_tanween():
    noon = tokenize("مِن")[0].letters[1]
    assert noon.is_bare
    assert not tokenize("إِنَّ")[0].letters[1].is_bare
    assert tokenize("أَحَدٌ")[0].letters[-1].has_tanween
