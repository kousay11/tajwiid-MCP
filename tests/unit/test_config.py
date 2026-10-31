import subprocess
import sys

import pytest

from wirdi_mcp.config import Settings


def test_environment_configuration_is_explicit_and_validated():
    assert Settings.from_env({}).log_level == "INFO"
    assert Settings.from_env({"WIRDI_MCP_LOG_LEVEL": "warning"}).log_level == "WARNING"
    with pytest.raises(ValueError, match="supported logging level"):
        Settings.from_env({"WIRDI_MCP_LOG_LEVEL": "secret-sentinel"})


def test_invalid_configuration_does_not_corrupt_protocol_stdout(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "wirdi_mcp.server"],
        cwd=tmp_path,
        env={"WIRDI_MCP_LOG_LEVEL": "secret-sentinel"},
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "supported logging level" in result.stderr
    assert "secret-sentinel" not in result.stderr


def test_quran_source_defaults_to_bundled_and_can_be_overridden_or_disabled(tmp_path):
    assert Settings.from_env({}).quran_source == "bundled"
    assert Settings.from_env({"WIRDI_AI_ROOT": str(tmp_path)}).quran_source == "external"
    assert Settings.from_env({"WIRDI_QURAN_SOURCE": "none"}).quran_source == "none"
    with pytest.raises(ValueError):
        Settings.from_env({"WIRDI_QURAN_SOURCE": "elsewhere"})
