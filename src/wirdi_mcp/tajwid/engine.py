"""Analysis service: verified Qaloun text + reading context + cited rules -> candidates.

Everything is deterministic and local. Annotations are always `candidate`: no reviewer
exists, so nothing here can be (or is) marked verified.
"""

import hashlib
from dataclasses import dataclass, field

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.domain.models import (
    EMITTABLE_STATUSES,
    PageRefs,
    QalounReference,
    ReadingContext,
    TajwidAnnotation,
    TextAnchor,
)
from wirdi_mcp.knowledge.models import TajwidRule
from wirdi_mcp.knowledge.registry import RuleRegistry
from wirdi_mcp.quran.source import PublicSourceRepository, SourceAyah
from wirdi_mcp.tajwid.detectors import (
    DETECTOR_VERSION,
    DETECTORS,
    AyahView,
    Occurrence,
    run_detectors,
)
from wirdi_mcp.tajwid.text import Letter, tokenize

GENERAL_LIMITATIONS = (
    "Every annotation is a candidate produced by a deterministic procedure; none is "
    "scholarly verified and no named reviewer exists.",
    "An empty or short result is not a claim that a passage has no Tajwid rules: only the "
    "listed rules are evaluated.",
    "The corpus tariq is unspecified. Rule sources attest Qaloun (book A) and Abu Nashit "
    "(book B); applying them to this corpus is a documented hypothesis.",
    "Waqf means the reading stops at the end of each selected ayah. Waqf signs inside an "
    "ayah are not treated as stops. `preceding` is accepted but no implemented rule uses it.",
)


@dataclass
class Verse:
    index: int  # position in the 6,214-ayah corpus
    row: SourceAyah
    sha256: str


@dataclass
class EngineResult:
    verses: list[Verse]
    occurrences: list[tuple[Verse, Occurrence]]
    rules: dict[str, TajwidRule]
    unresolved: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, int] = field(default_factory=dict)


class TajwidEngine:
    def __init__(self, repository: PublicSourceRepository, registry: RuleRegistry):
        self.repository = repository
        self.registry = registry
        self._references: dict[int, QalounReference] = {}  # immutable, so safe to share

    # -- rule selection ---------------------------------------------------------------
    def select_rules(
        self, rule_ids: tuple[str, ...], families: tuple[str, ...]
    ) -> dict[str, TajwidRule]:
        for rule_id in rule_ids:
            if rule_id not in DETECTORS:
                raise KnowledgeError("NOT_FOUND", "No detector exists for a requested rule")
        wanted = rule_ids or tuple(sorted(DETECTORS))
        rules = self.registry.get_rules(tuple((rid, DETECTORS[rid][1]) for rid in wanted))
        if families:
            rules = {rid: r for rid, r in rules.items() if r.family in families}
        return rules

    # -- verse selection --------------------------------------------------------------
    @staticmethod
    def load_verses(rows: tuple[SourceAyah, ...], first_index: int, last_index: int) -> list[Verse]:
        return [
            Verse(i, rows[i], hashlib.sha256(rows[i].text.encode("utf-8")).hexdigest())
            for i in range(first_index, last_index + 1)
        ]

    @staticmethod
    def locate(rows: tuple[SourceAyah, ...], surah: int, ayah: int) -> int:
        for i, row in enumerate(rows):
            if row.surah == surah and row.number == ayah:
                return i
        raise KnowledgeError("INVALID_REFERENCE", "Ayah is outside the Qaloun corpus")

    # -- detection --------------------------------------------------------------------
    def detect(
        self,
        rows: tuple[SourceAyah, ...],
        first_index: int,
        last_index: int,
        context: ReadingContext,
        rules: dict[str, TajwidRule],
    ) -> EngineResult:
        verses = self.load_verses(rows, first_index, last_index)
        wanted = frozenset(rules)
        result = EngineResult(verses, [], rules)
        following_letter = self._explicit_following(rows, last_index, context)
        for position, verse in enumerate(verses):
            last = position == len(verses) - 1
            words = tokenize(verse.row.text)
            stops_at_end = context.mode == "waqf"
            if last and context.stop_after_word is not None:
                words = words[: context.stop_after_word]
                stops_at_end = True
            next_first: Letter | None = None
            if not stops_at_end:
                if not last:
                    nxt = rows[verse.index + 1]
                    if nxt.surah == verse.row.surah:
                        next_first = self._first_letter(nxt.text)
                else:
                    next_first = following_letter
            view = AyahView(
                words=words,
                mode=context.mode,
                next_ayah_first=next_first,
                stops_at_end=stops_at_end,
                surah=verse.row.surah,
                ayah=verse.row.number,
                kufi=verse.row.links,
            )
            run_detectors(view, wanted)
            result.occurrences.extend((verse, o) for o in view.occurrences)
            for key, count in view.unresolved.items():
                result.unresolved[key] = result.unresolved.get(key, 0) + count
            for key, count in view.skipped.items():
                result.skipped[key] = result.skipped.get(key, 0) + count
        result.occurrences.sort(key=lambda vo: (vo[0].index, vo[1].start, vo[1].rule_id))
        return result

    @staticmethod
    def _first_letter(text: str) -> Letter | None:
        words = tokenize(text)
        return words[0].letters[0] if words else None

    def _explicit_following(
        self, rows: tuple[SourceAyah, ...], last_index: int, context: ReadingContext
    ) -> Letter | None:
        """The ayah after the selection is used only if the caller states it explicitly."""
        ref = context.following
        if ref is None or last_index + 1 >= len(rows):
            return None
        nxt = rows[last_index + 1]
        meta = self.repository.manifest["editions"]["qalun"]
        if (
            (ref.surah, ref.ayah) != (nxt.surah, nxt.number)
            or ref.numbering_system != meta["numbering_system"]
            or nxt.surah != rows[last_index].surah
        ):
            raise KnowledgeError(
                "INVALID_REFERENCE",
                "`following` must be the next ayah of the same surah in the Qaloun numbering",
            )
        return self._first_letter(nxt.text)

    # -- annotation building ----------------------------------------------------------
    def annotation(
        self,
        verse: Verse,
        occurrence: Occurrence,
        rule: TajwidRule,
        context: ReadingContext,
        pages: tuple[tuple[int, int], ...],
        pagination_sha256: str,
    ) -> TajwidAnnotation:
        reference = self._references.get(verse.index)
        if reference is None:
            reference = self.repository.reference("qalun", verse.row.surah, verse.row.number)
            assert isinstance(reference, QalounReference)
            self._references[verse.index] = reference
        start, end = pages[verse.index]
        annotation = TajwidAnnotation(
            annotation_id=(
                f"{rule.rule_id}:{rule.version}:{verse.row.surah}:{verse.row.number}:"
                f"{occurrence.start}-{occurrence.end}:{context.mode}"
            ),
            version=DETECTOR_VERSION,
            rule_id=rule.rule_id,
            rule_version=rule.version,
            anchor=TextAnchor(
                reference=reference,
                ayah_sha256=verse.sha256,
                start_codepoint=occurrence.start,
                end_codepoint=occurrence.end,
                word_index=occurrence.word_index,
            ),
            reading_context=context,
            detector_version=DETECTOR_VERSION,
            status="candidate",
            evidence=rule.evidence,
            page_refs=PageRefs(
                app_page_start=start, app_page_end=end, app_pagination_sha256=pagination_sha256
            ),
            note=occurrence.note,
            variants=occurrence.variants,
        )
        assert annotation.status in EMITTABLE_STATUSES
        return annotation
