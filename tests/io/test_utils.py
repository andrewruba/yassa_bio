from __future__ import annotations
from pathlib import Path
import pytest

from yassa_bio.io.utils import as_path


class TestAsPath:
    def test_relative_string_is_made_absolute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "file.txt").touch()

        result = as_path("file.txt")

        assert isinstance(result, Path)
        assert result.is_absolute()
        assert result == (tmp_path / "file.txt").resolve()

    def test_home_tilde_is_expanded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        fake_home = tmp_path / "home"
        monkeypatch.setenv("HOME", str(fake_home))
        target = "~/docs/report.csv"

        result = as_path(target)

        expected = fake_home / "docs" / "report.csv"
        assert result == expected.resolve()
        assert result.is_absolute()

    def test_path_instance_round_trips(self, tmp_path: Path):
        p = tmp_path / "data"
        result = as_path(p)
        assert result == p.expanduser().resolve()

    @pytest.mark.parametrize("bad", [123, 12.5, object(), ["list"]])
    def test_invalid_type_raises_typeerror(self, bad):
        with pytest.raises(TypeError):
            as_path(bad)
