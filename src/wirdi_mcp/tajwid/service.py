"""Application service behind the Tajwid tools: bounded, paged, typed results."""

from collections import Counter

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.domain.models import PassageSelection, Provenance, ReadingContext
from wirdi_mcp.knowledge.models import TajwidRule
from wirdi_mcp.knowledge.registry import RuleRegistry, digest
from wirdi_mcp.quran.source import PublicSourceRepository
from wirdi_mcp.tajwid.detectors import DETECTORS
from wirdi_mcp.tajwid.engine import GENERAL_LIMITATIONS, EngineResult, TajwidEngine
from wirdi_mcp.tools.contracts import (
    Analysis,
    AppPageAnalysis,
    AyahCounts,
    PageVerse,
    RuleList,
    RuleSummary,
    TajwidSummary,
)

MAX_SUMMARY_AYAT = 300


class TajwidService:
    def __init__(self, repository: PublicSourceRepository, registry: RuleRegistry):
        self.repository = repository
        self.registry = registry
        self.engine = TajwidEngine(repository, registry)

    # -- rules ------------------------------------------------------------------------
    def get_rule(self, rule_id: str, version: str) -> TajwidRule:
        return self.registry.get_rule(rule_id, version)

    def list_rules(self, family: str | None) -> RuleList:
        summaries = []
        for rule_id, version in self.registry.list_rules():
            rule = self.registry.get_rule(rule_id, version)
            if family is not None and rule.family != family:
                continue
            summaries.append(
                RuleSummary(
                    rule_id=rule.rule_id,
                    version=rule.version,
                    name_ar=rule.name_ar,
                    family=rule.family,
                    detectability=rule.detectability,
                    tariq=rule.tariq,
                    validation_status=rule.validation_status,
                    has_detector=rule.rule_id in DETECTORS,
                )
            )
        return RuleList(rules=tuple(summaries))

    def rules_provenance(self) -> Provenance:
        manifest = self.registry.manifest()
        raw = self.registry._read("rules/manifest.json")
        return Provenance(
            origin_id="wirdi-mcp:tajwid-rules",
            origin_version=manifest["manifest_version"],
            content_sha256=digest(raw),
        )

    # -- analysis ---------------------------------------------------------------------
    def analyze(
        self,
        selection: PassageSelection,
        context: ReadingContext,
        rule_ids: tuple[str, ...],
        families: tuple[str, ...],
        include_candidates: bool,
        limit: int,
        offset: int,
    ) -> Analysis:
        self.repository.validate_selection(selection)
        first = self.engine.locate(selection.start.surah, selection.start.ayah)
        last = self.engine.locate(selection.start.surah, selection.end_ayah)
        rules = self.engine.select_rules(rule_ids, families)
        result = self.engine.detect(first, last, context, rules)
        return self._assemble(result, context, include_candidates, limit, offset)

    def _assemble(
        self,
        result: EngineResult,
        context: ReadingContext,
        include_candidates: bool,
        limit: int,
        offset: int,
    ) -> Analysis:
        pages = self.repository.load_pages()
        pagination_sha = self.repository.manifest["pagination_sha256"]
        occurrences = result.occurrences if include_candidates else []
        window = occurrences[offset : offset + limit]
        annotations = tuple(
            self.engine.annotation(v, o, result.rules[o.rule_id], context, pages, pagination_sha)
            for v, o in window
        )
        end = offset + len(window)
        limitations = list(GENERAL_LIMITATIONS)
        if not include_candidates:
            limitations.append(
                "Only reviewed annotations were requested and none exists, so none is returned."
            )
        coverage = (
            "partial" if result.unresolved or not result.rules else "complete_for_requested_rules"
        )
        return Analysis(
            annotations=annotations,
            coverage=coverage if result.rules else "unsupported",
            evaluated_rule_versions=tuple(
                f"{r.rule_id}@{r.version}" for r in result.rules.values()
            ),
            limitations=tuple(limitations),
            total=len(occurrences),
            offset=offset,
            next_offset=end if end < len(occurrences) else None,
            rule_counts=dict(sorted(Counter(o.rule_id for _, o in result.occurrences).items())),
            unresolved=dict(sorted(result.unresolved.items())),
            skipped=dict(sorted(result.skipped.items())),
        )

    # -- summaries --------------------------------------------------------------------
    def summarize(
        self,
        surah: int,
        start_ayah: int | None,
        end_ayah: int | None,
        context: ReadingContext,
        rule_ids: tuple[str, ...],
        families: tuple[str, ...],
        limit: int,
        offset: int,
    ) -> TajwidSummary:
        count = self.repository.manifest["editions"]["qalun"]["surah_counts"][surah - 1]
        lo, hi = start_ayah or 1, end_ayah or count
        if not 1 <= lo <= hi <= count or hi - lo + 1 > MAX_SUMMARY_AYAT:
            raise KnowledgeError(
                "INVALID_REFERENCE", "Ayah range is outside the surah or too large"
            )
        rules = self.engine.select_rules(rule_ids, families)
        first, last = self.engine.locate(surah, lo), self.engine.locate(surah, hi)
        result = self.engine.detect(first, last, context, rules)
        per_verse: dict[int, Counter] = {v.index: Counter() for v in result.verses}
        for verse, occurrence in result.occurrences:
            per_verse[verse.index][occurrence.rule_id] += 1
        window = result.verses[offset : offset + limit]
        end = offset + len(window)
        return TajwidSummary(
            surah=surah,
            start_ayah=lo,
            end_ayah=hi,
            rule_counts=dict(sorted(Counter(o.rule_id for _, o in result.occurrences).items())),
            per_ayah=tuple(
                AyahCounts(
                    surah=v.row.surah,
                    ayah=v.row.number,
                    counts=dict(sorted(per_verse[v.index].items())),
                )
                for v in window
            ),
            total_ayat=len(result.verses),
            offset=offset,
            next_offset=end if end < len(result.verses) else None,
            evaluated_rule_versions=tuple(f"{r.rule_id}@{r.version}" for r in rules.values()),
            coverage="partial" if result.unresolved else "complete_for_requested_rules",
            unresolved=dict(sorted(result.unresolved.items())),
            limitations=GENERAL_LIMITATIONS,
        )

    # -- app pages --------------------------------------------------------------------
    def analyze_page(
        self,
        page: int,
        context: ReadingContext,
        rule_ids: tuple[str, ...],
        families: tuple[str, ...],
        limit: int,
        offset: int,
    ) -> AppPageAnalysis:
        pages = self.repository.load_pages()
        rows = self.repository.load_edition("qalun")
        owned = [i for i, (start, _end) in enumerate(pages) if start == page]
        continued = [i for i, (start, end) in enumerate(pages) if start < page <= end]
        rules = self.engine.select_rules(rule_ids, families)

        def verse(i: int) -> PageVerse:
            return PageVerse(
                surah=rows[i].surah,
                ayah=rows[i].number,
                page_start=pages[i][0],
                page_end=pages[i][1],
            )

        if owned:
            result = self.engine.detect(owned[0], owned[-1], context, rules)
            analysis = self._assemble(result, context, True, limit, offset)
        else:
            empty = EngineResult([], [], rules)
            analysis = self._assemble(empty, context, True, limit, offset)
        return AppPageAnalysis(
            page=page,
            pagination_status="verified_against_edition",
            verses=tuple(verse(i) for i in owned),
            continued_from_previous_page=tuple(verse(i) for i in continued),
            analysis=analysis,
        )
