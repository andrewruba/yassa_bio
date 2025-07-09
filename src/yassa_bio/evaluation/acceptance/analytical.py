from yassa_bio.pipeline.composite import CompositeStep


class Analytical(CompositeStep):
    def __init__(self) -> None:
        super().__init__(
            name="analytical",
            children=[],
        )
