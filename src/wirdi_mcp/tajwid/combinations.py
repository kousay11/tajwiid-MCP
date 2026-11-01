"""Legal combinations of readings inside one ayah (Nabhan pp.98-108, « ترتيب الأوجه » and
« تسوية المدود »).

Each madd occurrence lists its own `variants`; the book then says which choices may be taken
together. The tables below are the book's own lists, one per pair of madd kinds, in the order the
book gives them (iskan before sila, short before long). A pair the book lists is answered exactly.
For three or more positions the answer is the set of assignments in which every ordered pair obeys
its table, which extends the book's equalising rule (« same kind, same length ») and is marked as an
extension. A pair with no table is left free and said so. Nothing here chooses a reading.
"""

from dataclasses import dataclass
from itertools import product

# Position kinds, named by what the book calls them.
MUTTASIL = "muttasil"  # connected madd
MUNFASIL = "munfasil"  # separated madd
ARID_HAMZA = "muttasil_arid"  # connected madd made 'arid by the stop; needs the hamza's vowel
ARID = "arid_sukun"
LIN = "lin"
MEEM_KUBRA = "sila_kubra_meem"
MEEM_SUGHRA = "sila_sughra_meem"

RULE_KIND = {
    "madd_muttasil": MUTTASIL,
    "madd_munfasil": MUNFASIL,
    "madd_muttasil_arid": ARID_HAMZA,
    "madd_arid_sukun": ARID,
    "madd_lin": LIN,
    "madd_sila_kubra_meem": MEEM_KUBRA,
    "madd_sila_sughra_meem": MEEM_SUGHRA,
}
RELEVANT_RULES = tuple(RULE_KIND)

# Reading labels. A length is "{n}_harakat"; a stop on a hamza adds "+iskan", "+rawm" or "+ishmam".
H2, H3, H4, H6 = "2_harakat", "3_harakat", "4_harakat", "6_harakat"
ISKAN, SILA2, KUBRA = "iskan", "sila_2_harakat", "sila_kubra"


def _s(length: str, stop: str) -> str:
    return f"{length}+{stop}"


# (first kind, hamza vowel or None, second kind, hamza vowel or None) -> allowed pairs, book order.
def _pairs(rows: dict) -> list[tuple[str, str]]:
    return [(a, b) for a, bs in rows.items() for b in bs]


_EQUAL_UU = _pairs({H3: [H3], H4: [H4]})
_EQUAL_MM = _pairs({H2: [H2], H3: [H3], H4: [H4]})
_EQUAL_AA = _pairs({H2: [H2], H4: [H4], H6: [H6]})
_PAIRS: dict[tuple, list[tuple[str, str]]] = {
    # pp.100-101: the connected and the separated madd
    (MUTTASIL, None, MUTTASIL, None): _EQUAL_UU,
    (MUNFASIL, None, MUNFASIL, None): _EQUAL_MM,
    (MUTTASIL, None, MUNFASIL, None): _pairs({H4: [H4, H2], H3: [H3, H2]}),
    (MUNFASIL, None, MUTTASIL, None): _pairs({H2: [H3, H4], H3: [H3], H4: [H4]}),
    # p.102: a connected madd, then one made 'arid with a fatha on the hamza
    (MUTTASIL, None, ARID_HAMZA, "fatha"): _pairs(
        {H4: [_s(H4, ISKAN), _s(H6, ISKAN)], H3: [_s(H3, ISKAN), _s(H6, ISKAN)]}
    ),
    (MUNFASIL, None, ARID_HAMZA, "fatha"): _pairs(
        {
            H2: [_s(H3, ISKAN), _s(H4, ISKAN), _s(H6, ISKAN)],
            H3: [_s(H3, ISKAN), _s(H6, ISKAN)],
            H4: [_s(H4, ISKAN), _s(H6, ISKAN)],
        }
    ),
    # p.103: kasra on the hamza (the stop may be iskan or rawm)
    (MUTTASIL, None, ARID_HAMZA, "kasra"): _pairs(
        {
            H4: [_s(H4, ISKAN), _s(H6, ISKAN), _s(H4, "rawm")],
            H3: [_s(H3, ISKAN), _s(H6, ISKAN), _s(H3, "rawm")],
        }
    ),
    (MUNFASIL, None, ARID_HAMZA, "kasra"): _pairs(
        {
            H2: [_s(H3, ISKAN), _s(H4, ISKAN), _s(H6, ISKAN), _s(H3, "rawm"), _s(H4, "rawm")],
            H3: [_s(H3, ISKAN), _s(H6, ISKAN), _s(H3, "rawm")],
            H4: [_s(H4, ISKAN), _s(H6, ISKAN), _s(H4, "rawm")],
        }
    ),
    # pp.104-105: damma on the hamza (iskan, rawm or ishmam)
    (MUTTASIL, None, ARID_HAMZA, "damma"): _pairs(
        {
            H4: [
                _s(H4, ISKAN),
                _s(H6, ISKAN),
                _s(H4, "rawm"),
                _s(H4, "ishmam"),
                _s(H6, "ishmam"),
            ],
            H3: [
                _s(H3, "rawm"),
                _s(H3, "ishmam"),
                _s(H3, ISKAN),
                _s(H6, "ishmam"),
                _s(H6, ISKAN),
            ],
        }
    ),
    (MUNFASIL, None, ARID_HAMZA, "damma"): _pairs(
        {
            H2: [
                _s(H3, ISKAN),
                _s(H4, ISKAN),
                _s(H6, ISKAN),
                _s(H3, "ishmam"),
                _s(H4, "ishmam"),
                _s(H6, "ishmam"),
                _s(H3, "rawm"),
                _s(H4, "rawm"),
            ],
            H3: [_s(H3, ISKAN), _s(H6, ISKAN), _s(H3, "ishmam"), _s(H6, "ishmam"), _s(H3, "rawm")],
            H4: [_s(H4, ISKAN), _s(H6, ISKAN), _s(H4, "ishmam"), _s(H6, "ishmam"), _s(H4, "rawm")],
        }
    ),
    # pp.106-108: the 'arid madd and the lin madd, and each with itself
    (ARID, None, LIN, None): _pairs({H2: [H2], H4: [H4, H2], H6: [H6, H4, H2]}),
    (LIN, None, ARID, None): _pairs({H2: [H2, H4, H6], H4: [H4, H6], H6: [H6]}),
    (ARID, None, ARID, None): _EQUAL_AA,
    (LIN, None, LIN, None): _EQUAL_AA,
    # pp.98-99: plural meems (the sila before a hamza is the kubra, otherwise the sughra)
    (MEEM_KUBRA, None, MEEM_SUGHRA, None): _pairs({ISKAN: [ISKAN], SILA2: [SILA2], KUBRA: [SILA2]}),
    (MEEM_SUGHRA, None, MEEM_KUBRA, None): _pairs({ISKAN: [ISKAN], SILA2: [SILA2, KUBRA]}),
    (MUNFASIL, None, MEEM_SUGHRA, None): _pairs({H2: [ISKAN, SILA2], H4: [ISKAN, SILA2]}),
    (MEEM_SUGHRA, None, MUNFASIL, None): _pairs({ISKAN: [H2, H4], SILA2: [H2, H4]}),
}
# A pair of the same kind is also answered by the equalising table of that kind when the
# vowel of an 'arid hamza is not needed; the keys above already cover them.

# What each kind may read alone (the book's own lengths, p.32, p.34, p.98).
_DOMAIN: dict[tuple, tuple[str, ...]] = {
    (MUTTASIL, None): (H3, H4),
    (MUNFASIL, None): (H2, H3, H4),
    (ARID, None): (H2, H4, H6),
    (LIN, None): (H2, H4, H6),
    (MEEM_SUGHRA, None): (ISKAN, SILA2),
    (MEEM_KUBRA, None): (ISKAN, SILA2, KUBRA),
    (ARID_HAMZA, "fatha"): tuple(_s(h, ISKAN) for h in (H3, H4, H6)),
    (ARID_HAMZA, "kasra"): tuple(
        [_s(h, ISKAN) for h in (H3, H4, H6)] + [_s(h, "rawm") for h in (H3, H4)]
    ),
    (ARID_HAMZA, "damma"): tuple(
        [_s(h, ISKAN) for h in (H3, H4, H6)]
        + [_s(h, "rawm") for h in (H3, H4)]
        + [_s(h, "ishmam") for h in (H3, H4, H6)]
    ),
}
MAX_POSITIONS = 12


@dataclass(frozen=True)
class Position:
    rule_id: str
    kind: str
    vowel: str | None  # the hamza's vowel, for ARID_HAMZA only

    @property
    def key(self) -> tuple[str, str | None]:
        return (self.kind, self.vowel if self.kind == ARID_HAMZA else None)


@dataclass(frozen=True)
class Combinations:
    combinations: tuple[tuple[str, ...], ...]
    total: int
    truncated: bool
    basis: str  # single_position | book_listed | pairwise_extension | unconstrained
    notes: tuple[str, ...]


def combine(positions: list[Position], cap: int = 200) -> Combinations:
    notes: list[str] = []
    if not positions:
        return Combinations((), 0, False, "single_position", ())
    for p in positions:
        if p.key not in _DOMAIN:
            notes.append(
                f"{p.rule_id}: the hamza has no short vowel the book treats; readings are free"
                if p.kind == ARID_HAMZA
                else f"{p.rule_id}: no readings known"
            )
    known = [p for p in positions if p.key in _DOMAIN]
    if len(positions) > MAX_POSITIONS:
        return Combinations(
            (), 0, True, "unconstrained", ("too many madds in one ayah to combine; readings free",)
        )
    if len(known) != len(positions):
        return Combinations((), 0, False, "unconstrained", tuple(notes))
    if len(known) == 1:
        domain = _DOMAIN[known[0].key]
        return Combinations(tuple((r,) for r in domain), len(domain), False, "single_position", ())
    pairs_seen = 0
    pairs_listed = 0
    allowed: dict[tuple[int, int], list[tuple[str, str]] | None] = {}
    for i, a in enumerate(known):
        for j in range(i + 1, len(known)):
            table = _PAIRS.get((*a.key, *known[j].key))
            allowed[(i, j)] = table
            pairs_seen += 1
            pairs_listed += table is not None
    if len(known) == 2 and pairs_listed == 1:
        table = allowed[(0, 1)]
        assert table is not None
        total = len(table)
        return Combinations(tuple(table[:cap]), total, total > cap, "book_listed", ())
    results: list[tuple[str, ...]] = []
    total = 0
    for assignment in product(*(_DOMAIN[p.key] for p in known)):
        ok = all(
            table is None or (assignment[i], assignment[j]) in table
            for (i, j), table in allowed.items()
        )
        if ok:
            total += 1
            if len(results) < cap:
                results.append(assignment)
    if pairs_listed == 0:
        notes.append("the book gives no table for these kinds together, so the readings are free")
        basis = "unconstrained"
    else:
        if pairs_listed < pairs_seen:
            notes.append("some pairs have no table in the book and are left free")
        notes.append(
            "three or more madds: every pair obeys the book's table (an extension of its "
            "equalising rule)"
        )
        basis = "pairwise_extension"
    return Combinations(tuple(results), total, total > cap, basis, tuple(notes))
