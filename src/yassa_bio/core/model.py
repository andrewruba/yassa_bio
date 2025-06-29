from pydantic import BaseModel


class SchemaModel(BaseModel):
    model_config = {
        "extra": "forbid",
        "strict": False,
        "frozen": True,
    }
