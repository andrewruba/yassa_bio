from yassa_bio.core.registry import register

from yassa_bio.pipeline.composite import CompositeStep


@register("curve_model", "4PL")
class FourPLModel:
    def fit(self, x, y, w):
        pass

    def predict(self, x):
        pass


class Fit(CompositeStep):
    def __init__(self) -> None:
        super().__init__(
            name="fit",
            children=[],
        )
