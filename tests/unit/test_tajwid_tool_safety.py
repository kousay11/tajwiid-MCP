import json

from wirdi_mcp.domain.exceptions import KnowledgeError
from wirdi_mcp.tools.tajwid import _guard


def payload(result):
    return json.dumps(result.structured_content, ensure_ascii=False)


def test_unexpected_exception_never_echoes_internals():
    def boom():
        raise RuntimeError("secret /home/someone/private/path and book text")

    result = _guard(boom)
    assert result.is_error
    text = payload(result)
    assert "secret" not in text and "/home" not in text
    assert result.structured_content["error"]["code"] == "DATA_UNAVAILABLE"


def test_typed_errors_pass_through_unchanged():
    def missing():
        raise KnowledgeError("NOT_FOUND", "No such local Tajwid rule")

    result = _guard(missing)
    assert result.structured_content["error"] == {
        "code": "NOT_FOUND",
        "message": "No such local Tajwid rule",
        "retryable": False,
    }


def test_invalid_parameters_are_a_typed_error_without_the_input_value():
    from wirdi_mcp.tools.contracts import SummaryInput

    def invalid():
        SummaryInput(surah=999, reading_context={"mode": "waqf"})
        raise AssertionError("not reached")

    result = _guard(invalid)
    assert result.structured_content["error"]["code"] == "INVALID_REFERENCE"
    assert "999" not in payload(result)
