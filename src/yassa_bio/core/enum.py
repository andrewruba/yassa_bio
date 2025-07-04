from enum import StrEnum


class DescribedStrEnum(StrEnum):
    """Base-class that adds a .desc attribute to each member."""

    desc: str

    def __new__(cls, value: str, desc: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.desc = desc
        return obj


def enum_examples(ecls):
    return [m.value for m in ecls]
