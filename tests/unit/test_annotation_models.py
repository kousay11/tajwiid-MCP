import pytest
from pydantic import ValidationError

from wirdi_mcp.domain.models import (
    EMITTABLE_STATUSES,
    ImageProvenance,
    ObservedColor,
    PageRefs,
    TajwidAnnotation,
)


def ref():
    return {
        "corpus_id": "synthetic",
        "corpus_version": "v1",
        "numbering_system": "synthetic-numbering",
        "riwaya": "qaloun",
        "tariq": "unspecified",
        "surah": 1,
        "ayah": 1,
    }


def citation():
    return {
        "source_id": "synthetic",
        "edition_id": "synthetic",
        "title": "Fixture",
        "responsible_party": "Fixture",
        "publication": "Fixture",
        "locator": "p. 1",
        "riwaya": "qaloun",
        "tariq": "unspecified",
        "provenance_version": "v1",
        "validation_status": "unreviewed",
    }


def base(**changes):
    value = {
        "annotation_id": "a",
        "version": "1",
        "rule_id": "r",
        "rule_version": "1",
        "anchor": {
            "reference": ref(),
            "ayah_sha256": "0" * 64,
            "start_codepoint": 0,
            "end_codepoint": 1,
            "word_index": 1,
        },
        "reading_context": {"mode": "waqf", "basis": "source_default"},
        "status": "candidate",
        "detector_version": "d1",
        "evidence": (citation(),),
    }
    value.update(changes)
    return value


IMAGE = ImageProvenance(
    edition_id="mushaf-hannibal",
    pdf_page=300,
    printed_page="299",
    bbox=(10, 10, 20, 20),
    image_sha256="1" * 64,
    extractor_version="x1",
)
COLOR = ObservedColor(color_id=2, rgb=(200, 20, 30), pixel_count=40)


def test_candidate_needs_rule_and_detector():
    TajwidAnnotation.model_validate(base())
    with pytest.raises(ValidationError, match="candidate needs a rule"):
        TajwidAnnotation.model_validate(base(detector_version=None))


def test_rule_id_is_nullable_only_with_a_legend_class():
    with pytest.raises(ValidationError, match="rule or a legend class"):
        TajwidAnnotation.model_validate(
            base(rule_id=None, rule_version=None, status="unsupported_context")
        )
    annotation = TajwidAnnotation.model_validate(
        base(
            rule_id=None,
            rule_version=None,
            legend_class_id="red",
            status="source_annotated",
            detector_version=None,
            image=IMAGE,
            observed_color=COLOR,
        )
    )
    assert annotation.rule_id is None


def test_rule_id_and_version_travel_together():
    with pytest.raises(ValidationError, match="together"):
        TajwidAnnotation.model_validate(base(rule_version=None))


def test_source_derived_status_needs_image_and_colour():
    with pytest.raises(ValidationError, match="observed colour"):
        TajwidAnnotation.model_validate(base(status="source_annotated"))
    TajwidAnnotation.model_validate(base(status="cross_checked", image=IMAGE, observed_color=COLOR))


def test_verified_is_never_emittable():
    assert "scholarly_verified" not in EMITTABLE_STATUSES
    assert {
        "candidate",
        "cross_checked",
        "conflict",
        "not_annotated_in_source",
    } <= EMITTABLE_STATUSES
    with pytest.raises(ValidationError, match="validation records"):
        TajwidAnnotation.model_validate(base(status="scholarly_verified"))


def test_page_refs_keep_both_paginations_and_bounds():
    refs = PageRefs(
        app_page_start=263, app_page_end=264, source_page_pdf=300, source_page_printed="299"
    )
    assert refs.app_page_end == 264 and refs.source_page_printed == "299"
    with pytest.raises(ValidationError):
        PageRefs(app_page_start=560)


def test_image_bbox_must_be_a_rectangle():
    with pytest.raises(ValidationError):
        ImageProvenance(
            edition_id="e",
            pdf_page=1,
            bbox=(5, 5, 5, 9),
            image_sha256="1" * 64,
            extractor_version="x",
        )
