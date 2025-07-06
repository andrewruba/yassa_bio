import pytest
from pydantic import ValidationError

from yassa_bio.core.model import SchemaModel


class TestSchemaModel:
    class Demo(SchemaModel):
        x: int
        y: float = 1.5

    @pytest.mark.parametrize("bad_payload", [{"x": "5"}, {"x": 1, "y": "3.2"}])
    def test_accepts_coercion(self, bad_payload):
        d = self.Demo(**bad_payload)
        assert isinstance(d.x, int) and isinstance(d.y, float)

    def test_valid_payload_passes(self):
        d = self.Demo(x=3, y=2.5)
        assert d.x == 3 and d.y == 2.5

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            self.Demo(x=1, z=99)

    def test_instance_is_not_frozen(self):
        d = self.Demo(x=4)

        d.x = 10
        assert d.x == 10

        d2 = d.model_copy(update={"y": 9.9})
        assert d2.y == 9.9
        assert d.y == 1.5
