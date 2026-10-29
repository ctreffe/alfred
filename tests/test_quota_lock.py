from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import alfred3.quota as quota_module
from alfred3.quota import QuotaIO


def test_late_successful_acquisition_enters_and_releases(monkeypatch):
    clock = SimpleNamespace(time=Mock(side_effect=[0, 31]), sleep=Mock())
    monkeypatch.setattr(quota_module, "time", clock)
    io = QuotaIO.__new__(QuotaIO)
    io.exp = SimpleNamespace(log=SimpleNamespace(debug=Mock()))
    owned = object()
    io.load_markbusy = Mock(side_effect=[None] * 6 + [owned])
    io.release = Mock()

    with io as data:
        assert data is owned
        io.release.assert_not_called()

    assert io.load_markbusy.call_count == 7
    io.release.assert_called_once_with()


def test_timeout_does_not_release_an_unacquired_lock(monkeypatch):
    clock = SimpleNamespace(time=Mock(side_effect=[0, 31]), sleep=Mock())
    monkeypatch.setattr(quota_module, "time", clock)
    io = QuotaIO.__new__(QuotaIO)
    io.exp = SimpleNamespace(log=SimpleNamespace(debug=Mock()))
    io.load_markbusy = Mock(return_value=None)
    io.release = Mock()

    with pytest.raises(RuntimeError, match="always busy"):
        with io:
            pytest.fail("A busy quota must not enter its context")

    io.release.assert_not_called()
