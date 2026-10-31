import pytest
from pydantic import TypeAdapter, ValidationError

from wirdi_mcp.domain.models import PassageSelection, QalounReference, TajwidAnnotation, TextAnchor
from wirdi_mcp.tools.contracts import TOOL_CONTRACTS


def reference(**changes):
    return {
        "corpus_id": "synthetic-fixture",
        "corpus_version": "test-v1",
        "numbering_system": "synthetic-numbering",
        "riwaya": "qaloun",
        "tariq": "abu_nashit",
        "surah": 1,
        "ayah": 1,
        **changes,
    }


@pytest.mark.parametrize("missing", ["corpus_id", "corpus_version", "numbering_system", "riwaya"])
def test_reference_never_infers_corpus_or_numbering(missing):
    value = reference()
    del value[missing]
    with pytest.raises(ValidationError):
        QalounReference.model_validate(value)


@pytest.mark.parametrize("changes", [{"riwaya": "hafs"}, {"tariq": "unknown"}, {"ayah": True}])
def test_reference_rejects_incompatible_identity(changes):
    with pytest.raises(ValidationError):
        QalounReference.model_validate(reference(**changes))


@pytest.mark.parametrize("end_ayah", [0, 101])
def test_selection_requires_ordered_bounded_range(end_ayah):
    with pytest.raises(ValidationError):
        PassageSelection(start=reference(), end_ayah=end_ayah)


def test_unreviewed_occurrence_cannot_claim_scholarly_verification():
    anchor = TextAnchor(
        reference=reference(),
        ayah_sha256="0" * 64,
        start_codepoint=0,
        end_codepoint=1,
        word_index=1,
    )
    with pytest.raises(ValidationError, match="scholarly validation records"):
        TajwidAnnotation(
            annotation_id="synthetic",
            version="test-v1",
            rule_id="synthetic",
            rule_version="test-v1",
            anchor=anchor,
            reading_context={"mode": "wasl"},
            status="scholarly_verified",
            evidence=(
                {
                    "source_id": "synthetic",
                    "edition_id": "synthetic",
                    "title": "Fixture",
                    "responsible_party": "Fixture",
                    "publication": "Fixture",
                    "locator": "test",
                    "riwaya": "qaloun",
                    "tariq": "abu_nashit",
                    "provenance_version": "test-v1",
                    "validation_status": "unreviewed",
                },
            ),
        )


def test_all_local_tool_contracts_have_serializable_input_and_output_schemas():
    assert len(TOOL_CONTRACTS) == 10
    for input_model, output_type, phase in TOOL_CONTRACTS.values():
        assert input_model.model_json_schema()["type"] == "object"
        assert TypeAdapter(output_type).json_schema()["anyOf"]
        assert phase > 1
