# tests/test_core_enum.py
import pytest
from enum import Enum

from yassa_bio.core.enum import DescribedStrEnum, enum_examples


class ToyEnum(DescribedStrEnum):
    ALPHA = ("α", "First letter of Greek alphabet")
    BETA = ("β", "Second letter of Greek alphabet")
    GAMMA = ("γ", "Third letter of Greek alphabet")


class TestDescribedStrEnum:
    def test_value_and_desc_attributes(self):
        assert ToyEnum.ALPHA.value == "α"
        assert ToyEnum.ALPHA.desc == "First letter of Greek alphabet"

    def test_iter_preserves_order(self):
        assert [m.value for m in ToyEnum] == ["α", "β", "γ"]

    def test_enum_examples_helper(self):
        assert enum_examples(ToyEnum) == ["α", "β", "γ"]

    def test_comparison_behaves_like_str(self):
        assert ToyEnum.BETA == "β"
        assert "β" in {ToyEnum.BETA}

    def test_wrong_constructor_arguments_raise(self):
        with pytest.raises(TypeError):

            class BadEnum(DescribedStrEnum):
                OOPS = ("only-one-arg",)


class TestEnumExamplesUtility:
    class Numbers(Enum):
        ONE = 1
        TWO = 2

    def test_enum_examples_plain_enum(self):
        assert enum_examples(self.Numbers) == [1, 2]
