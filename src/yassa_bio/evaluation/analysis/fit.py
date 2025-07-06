from yassa_bio.core.registry import register


@register("curve_model", "4PL")
class FourPLModel:
    def fit(self, x, y, w):
        pass

    def predict(self, x):
        pass
