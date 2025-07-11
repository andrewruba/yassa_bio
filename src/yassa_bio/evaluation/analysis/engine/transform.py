import numpy as np

from yassa_bio.schema.analysis.enum import Transformation
from yassa_bio.core.registry import register


@register("transform", Transformation.IDENTITY)
def transform_identity(x: np.ndarray) -> np.ndarray:
    return x


@register("transform", Transformation.LN)
def transform_ln(x: np.ndarray) -> np.ndarray:
    return np.log(x)


@register("transform", Transformation.LOG2)
def transform_log2(x: np.ndarray) -> np.ndarray:
    return np.log2(x)


@register("transform", Transformation.LOG10)
def transform_log10(x: np.ndarray) -> np.ndarray:
    return np.log10(x)


@register("transform", Transformation.SQRT)
def transform_sqrt(x: np.ndarray) -> np.ndarray:
    return np.sqrt(x)


@register("transform", Transformation.RECIPROCAL)
def transform_reciprocal(x: np.ndarray) -> np.ndarray:
    return 1 / x
