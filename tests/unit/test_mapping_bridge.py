from types import SimpleNamespace

import pytest

from wirdi_mcp.mapping.bridge import ReadOnlyAuthorityView, _AyahType, _QuranEditionType, _select
from wirdi_mcp.quran.source import SourceAyah


def test_bridge_allows_only_observed_reads_and_detaches_links():
    row = SourceAyah(112, 1, "SENTINEL", (1,))
    view = ReadOnlyAuthorityView({"qalun": (row,), "hafs": ()}, {"qalun": {"source": "test"}})
    result = view.select_qaloun(112, 1, 1)
    result[0].number_in_hafs.append(999)
    assert view.select_qaloun(112, 1, 1)[0].number_in_hafs == [1]
    assert view.get(_QuranEditionType, "qalun").source == "test"
    with pytest.raises(RuntimeError):
        _select(SimpleNamespace)
    with pytest.raises(RuntimeError):
        _select(_AyahType).where(_AyahType.surah == 112)
    with pytest.raises(RuntimeError):
        view.scalars(_select(_AyahType))
    assert not hasattr(view, "execute") and not hasattr(view, "commit")
