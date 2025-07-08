from __future__ import annotations
import pytest

import yassa_bio.core.registry as _reg


class TestRegistry:
    @pytest.fixture(autouse=True)
    def isolate_registry(self):
        """
        Start every test with an empty registry, but put the original
        entries (CSV/Excel readers, etc.) back when the test is done so
        the global test suite is unaffected.
        """
        snapshot = _reg._registry.copy()
        _reg._registry.clear()
        try:
            yield
        finally:
            _reg._registry.clear()
            _reg._registry.update(snapshot)

    @staticmethod
    def _dummy(kind: str, name: str):
        @_reg.register(kind, name)
        def _fn():
            pass

        return _fn

    def test_register_and_get_function(self):
        fn = self._dummy("mask", "zscore")
        assert _reg.get("mask", "zscore") is fn

    def test_register_and_get_class(self):
        @_reg.register("model", "4pl")
        class Model4PL:
            pass

        assert _reg.get("model", "4pl") is Model4PL

    def test_case_insensitive_lookup(self):
        fn = self._dummy("MASK", "ZScore")
        assert _reg.get("mask", "zscore") is fn
        assert _reg.get("MaSk", "ZsCoRe") is fn

    def test_duplicate_registration_raises(self):
        self._dummy("norm", "mean")
        with pytest.raises(KeyError, match="already registered"):
            self._dummy("Norm", "Mean")

    def test_missing_key_error_lists_available(self):
        self._dummy("outlier", "iqr")
        with pytest.raises(KeyError) as exc:
            _reg.get("outlier", "grubbs")

        msg = str(exc.value).lower()
        assert "grubbs" in msg and "iqr" in msg

    def test_registry_state_private(self):
        self._dummy("foo", "bar")
        assert list(_reg._registry.keys()) == [("foo", "bar")]
