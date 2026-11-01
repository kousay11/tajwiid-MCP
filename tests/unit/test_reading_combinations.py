"""The combination tables must give exactly the counts the book states (Nabhan pp.98-108)."""

import pytest

from wirdi_mcp.tajwid.combinations import (
    ARID,
    ARID_HAMZA,
    LIN,
    MEEM_KUBRA,
    MEEM_SUGHRA,
    MUNFASIL,
    MUTTASIL,
    Position,
    combine,
)


def pos(kind, vowel=None):
    return Position("rule", kind, vowel)


@pytest.mark.parametrize(
    ("first", "second", "count"),
    [
        (pos(MUTTASIL), pos(MUTTASIL), 2),  # p.100: equal lengths
        (pos(MUNFASIL), pos(MUNFASIL), 3),  # p.101
        (pos(MUTTASIL), pos(MUNFASIL), 4),  # p.101 a
        (pos(MUNFASIL), pos(MUTTASIL), 4),  # p.101 b
        (pos(MUTTASIL), pos(ARID_HAMZA, "fatha"), 4),  # p.102: « أربعة أوجه »
        (pos(MUNFASIL), pos(ARID_HAMZA, "fatha"), 7),  # p.102: « سبعة أوجه »
        (pos(MUTTASIL), pos(ARID_HAMZA, "kasra"), 6),  # p.103: « ستة أوجه »
        (pos(MUNFASIL), pos(ARID_HAMZA, "kasra"), 11),  # p.103: « أحد عشر وجها »
        (pos(MUTTASIL), pos(ARID_HAMZA, "damma"), 10),  # p.104: « عشرة وجوه »
        (pos(MUNFASIL), pos(ARID_HAMZA, "damma"), 18),  # p.105: « ثمانية عشر وجها »
        (pos(ARID), pos(LIN), 6),  # p.106
        (pos(LIN), pos(ARID), 6),  # p.106-107
        (pos(ARID), pos(ARID), 3),  # p.107
        (pos(LIN), pos(LIN), 3),  # p.108
        (pos(MEEM_KUBRA), pos(MEEM_SUGHRA), 3),  # p.98: « ثلاثة أوجه »
        (pos(MEEM_SUGHRA), pos(MEEM_KUBRA), 3),  # p.98
        (pos(MUNFASIL), pos(MEEM_SUGHRA), 4),  # p.98-99: « أربعة أوجه »
        (pos(MEEM_SUGHRA), pos(MUNFASIL), 4),  # p.99
    ],
)
def test_a_pair_gives_the_number_of_readings_the_book_states(first, second, count):
    result = combine([first, second])
    assert result.total == count == len(result.combinations)
    assert result.basis == "book_listed" and not result.truncated


def test_the_book_orders_iskan_before_sila_and_short_before_long():
    kubra_sughra = combine([pos(MEEM_KUBRA), pos(MEEM_SUGHRA)]).combinations
    assert kubra_sughra[0] == ("iskan", "iskan")
    assert combine([pos(MUNFASIL), pos(MUNFASIL)]).combinations[0] == ("2_harakat", "2_harakat")


def test_one_position_lists_its_own_readings_and_chooses_none():
    result = combine([pos(MUNFASIL)])
    assert [c[0] for c in result.combinations] == ["2_harakat", "3_harakat", "4_harakat"]
    assert result.basis == "single_position"


def test_three_madds_extend_the_equalising_rule_and_say_so():
    result = combine([pos(MUTTASIL), pos(MUTTASIL), pos(MUTTASIL)])
    assert result.total == 2  # all three equal: 3-3-3 or 4-4-4
    assert result.basis == "pairwise_extension"
    assert any("extension" in note for note in result.notes)


def test_kinds_the_book_gives_no_table_for_stay_free():
    result = combine([pos(MUTTASIL), pos(LIN)])
    assert result.basis == "unconstrained" and result.total == 2 * 3


def test_an_arid_hamza_without_a_short_vowel_is_left_free():
    result = combine([pos(MUTTASIL), pos(ARID_HAMZA, None)])
    assert result.basis == "unconstrained" and result.combinations == ()


def test_a_cap_truncates_without_changing_the_total():
    result = combine([pos(MUNFASIL), pos(ARID_HAMZA, "damma")], cap=5)
    assert result.total == 18 and len(result.combinations) == 5 and result.truncated
