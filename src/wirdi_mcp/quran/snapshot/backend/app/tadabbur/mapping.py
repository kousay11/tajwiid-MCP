"""Conservative, read-only correspondence of edition-specific ayah boundaries.

Stored links propose connected passages; complete component texts must then agree
under the documented orthographic skeleton comparison. No fuzzy match certifies a
mapping. This verifies passage boundaries, NOT identity of readings or word offsets.
"""
import unicodedata

from sqlalchemy import select

from ..models import Ayah, QuranEdition
from ..schemas import MappingOut, PassageReference
from .arabic import normalize

REVIEW = "لم نتمكّن من التحقّق من مطابقة المقطع لمراجع التفسير؛ لم نجلب تعليقًا قد يُنسب إلى آيات غير مطابقة."
CHECKSUMS = {
    "qalun": "ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
    "hafs": "0136b913aeb5a6a0389681f988215791ddd848c4347f7cf5e9d2574db7f1da49",
}


def skeleton(text: str) -> str:
    # Comparison copies only. Source/stored/displayed text is NEVER transformed.
    # Qaloun uses U+06D2 for ya; spacing/marks differ between the two transcriptions.
    return "".join(c for c in normalize(text).replace("ے", "ي") if unicodedata.category(c).startswith("L"))


def ref(edition, surah, nums):
    return PassageReference(edition_id=edition, surah=surah, from_ayah=min(nums), to_ayah=max(nums))


def range_string(r: PassageReference) -> str:
    return f"{r.surah}:{r.from_ayah}" + (f"-{r.to_ayah}" if r.to_ayah != r.from_ayah else "")


def resolve(db, ayat, edition, surah) -> MappingOut:
    selection = {a.number for a in ayat}
    canonical = ref("qalun", surah, selection) if edition == "qalun" else None
    provenance = {"method": "linked_components_and_exact_orthographic_skeleton_v1", "scope": "passage_boundaries_not_reading_identity", "editions": {}}
    out = MappingOut(qaloun_reference=canonical, mapping_status="mapping_requires_review", mapping_type="unverified", source_provenance=provenance, user_notice=REVIEW)
    for eid in ("qalun", "hafs"):
        ed = db.get(QuranEdition, eid)
        if ed:
            provenance["editions"][eid] = {"source": ed.source, "source_checksum": ed.source_checksum, "text_checksum": ed.text_checksum, "license": ed.license}
        if ed is None or ed.source_checksum != CHECKSUMS[eid]:
            out.reasons.append(f"unverified_edition:{eid}")
    if out.reasons:
        return out
    if edition == "hafs":  # retained API compatibility; never offered in the Qaloun UI
        out.source_reference = [ref("hafs", surah, selection)]
        out.mapping_status, out.mapping_type = "verified_equivalent", "exact"
        out.requires_user_notice, out.user_notice = False, None
        return out
    q = {a.number: a for a in db.scalars(select(Ayah).where(Ayah.edition_id == "qalun", Ayah.surah == surah))}
    h = {a.number: a for a in db.scalars(select(Ayah).where(Ayah.edition_id == "hafs", Ayah.surah == surah))}
    links = {n: set(a.number_in_hafs) if isinstance(a.number_in_hafs, list) and all(type(v) is int for v in a.number_in_hafs) else set() for n, a in q.items()}
    # The stored Fatiha link includes the Hafs basmala. Narrow ONLY with textual evidence.
    if surah == 1 and links.get(1) == {1, 2} and 2 in h and skeleton(q[1].text) == skeleton(h[2].text):
        links[1] = {2}
        out.source_provenance["fatiha_basmala"] = "excluded_by_complete_text_comparison"
    remaining, source, types = set(selection), set(), set()
    while remaining:
        qs, hs = {min(remaining)}, set()
        while True:
            next_h = set().union(*(links[n] for n in qs))
            next_q = qs | {n for n in q if links[n] & next_h}
            if next_h == hs and next_q == qs:
                break
            qs, hs = next_q, next_h
        remaining -= qs
        if not hs:
            out.mapping_type = "missing"
            out.reasons.append(f"missing_links:{min(qs)}")
            continue
        source |= hs
        kind = "exact" if len(qs) == len(hs) == 1 else "one_to_many" if len(qs) == 1 else "many_to_one" if len(hs) == 1 else "many_to_many"
        contiguous = (sorted(qs) == list(range(min(qs), max(qs) + 1)) and sorted(hs) == list(range(min(hs), max(hs) + 1)))
        valid_links = all(links[n] and links[n] <= h.keys() and sorted(links[n]) == list(range(min(links[n]), max(links[n]) + 1)) for n in qs)
        ordered = all(min(links[a]) <= min(links[b]) and max(links[a]) <= max(links[b]) for a,b in zip(sorted(qs), sorted(qs)[1:])) if valid_links else False
        # An overlapping many-to-many allocation cannot be certified by matching
        # the outer envelope alone; its internal boundaries require review.
        same = kind != "many_to_many" and valid_links and contiguous and ordered and skeleton(" ".join(q[n].text for n in sorted(qs))) == skeleton(" ".join(h[n].text for n in sorted(hs)))
        if kind == "exact" and qs != hs:
            kind = "numbering"
        types.add(kind)
        out.components.append({"qaloun_ayat": sorted(qs), "source_ayat": sorted(hs), "type": kind, "textual_boundary_verified": bool(same), "includes_context_outside_selection": not qs <= selection})
        if not same:
            out.reasons.append(f"unverified_component:{min(qs)}")
    # Keep distinct source ranges; never inflate a set into an unchecked min/max envelope.
    for n in sorted(source):
        if out.source_reference and n == out.source_reference[-1].to_ayah + 1:
            out.source_reference[-1].to_ayah = n
        else:
            out.source_reference.append(ref("hafs", surah, {n}))
    if out.reasons:
        if out.mapping_type != "missing":
            out.mapping_type = "ambiguous" if any(c["type"] == "many_to_many" for c in out.components) else "unverified"
        return out
    out.mapping_type = next(iter(types)) if len(types) == 1 else "mixed"
    exact = all(c["type"] == "exact" for c in out.components)
    out.mapping_status = "verified_equivalent" if exact else "verified_difference"
    out.requires_user_notice = not exact
    if exact:
        out.user_notice = None
    else:
        ranges = "، ".join(range_string(r) for r in out.source_reference)
        boundary = next((c for c in out.components if c["type"] not in {"exact", "numbering"}), None)
        out.user_notice = f"المقطع المختار بترقيم قالون يقابله في مصدر التفسير \u2066{ranges}\u2069 بترقيم حفص."
        if boundary:
            qr = range_string(ref("qalun", surah, boundary["qaloun_ayat"]))
            hr = range_string(ref("hafs", surah, boundary["source_ayat"]))
            out.user_notice += f" تختلف حدود الآيات هنا: \u2066{qr}\u2069 بترقيم قالون تقابل \u2066{hr}\u2069 في المصدر."
        else:
            out.user_notice += " تختلف أرقام الآيات في هذا المقطع."
        if any(c["includes_context_outside_selection"] for c in out.components):
            out.user_notice += " يشمل التعليق سياق الآية المصدرية كاملةً، وهو أوسع من الاختيار."
    return out
