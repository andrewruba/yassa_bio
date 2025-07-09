from yassa_bio.pipeline.composite import CompositeStep


class Validation(CompositeStep):
    def __init__(self) -> None:
        super().__init__(
            name="validation",
            children=[],
        )
