import numpy as np

from yassa_bio.schema.analysis.enum import Weighting
from yassa_bio.core.registry import register


@register("weighting", Weighting.ONE)
def weight_one(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.ones_like(y)


@register("weighting", Weighting.ONE_OVER_X)
def weight_one_over_x(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return 1.0 / x


@register("weighting", Weighting.ONE_OVER_X2)
def weight_one_over_x2(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return 1.0 / (x**2)


@register("weighting", Weighting.ONE_OVER_Y)
def weight_one_over_y(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return 1.0 / y


@register("weighting", Weighting.ONE_OVER_Y2)
def weight_one_over_y2(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return 1.0 / (y**2)
