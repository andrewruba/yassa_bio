from scipy.optimize import curve_fit
import numpy as np

from yassa_bio.core.registry import register
from yassa_bio.schema.analysis.enum import CurveModel


def _4pl(x, a, b, c, d):
    return d + (a - d) / (1 + (x / c) ** b)


def _5pl(x, a, b, c, d, g):
    return d + (a - d) / ((1 + (x / c) ** b) ** g)


def _linear(x, m, b):
    return m * x + b


def _inv_4pl(y, a, b, c, d):
    y = np.clip(y, min(a, d) + 1e-10, max(a, d) - 1e-10)
    denom = (a - d) / (y - d) - 1
    return c * np.power(denom, 1 / b)


def _inv_5pl(y, a, b, c, d, g):
    y = np.clip(y, min(a, d) + 1e-10, max(a, d) - 1e-10)
    ratio = (a - d) / (y - d)
    inner = np.power(ratio, 1 / g) - 1
    return c * np.power(inner, 1 / b)


def _inv_linear(y, m, b):
    return (y - b) / m


@register("curve_model", CurveModel.FOUR_PL)
def fit_4pl(x: np.ndarray, y: np.ndarray, weights: np.ndarray = None):
    lower = [-np.inf, -np.inf, 1e-12, -np.inf]
    upper = [np.inf, np.inf, np.inf, np.inf]
    popt, _ = curve_fit(
        _4pl,
        x,
        y,
        p0=[min(y), 1.0, np.median(x), max(y)],
        bounds=(lower, upper),
        sigma=1 / np.sqrt(weights),
        absolute_sigma=True,
    )
    return lambda x: _4pl(x, *popt), popt


@register("curve_model", CurveModel.FIVE_PL)
def fit_5pl(x: np.ndarray, y: np.ndarray, weights: np.ndarray = None):
    lower = [-np.inf, -np.inf, 1e-12, -np.inf, -np.inf]
    upper = [np.inf, np.inf, np.inf, np.inf, np.inf]
    popt, _ = curve_fit(
        _5pl,
        x,
        y,
        p0=[min(y), 1.0, np.median(x), max(y), 1.0],
        bounds=(lower, upper),
        sigma=1 / np.sqrt(weights),
        absolute_sigma=True,
    )
    return lambda x: _5pl(x, *popt), popt


@register("curve_model", CurveModel.LINEAR)
def fit_linear(x: np.ndarray, y: np.ndarray, weights: np.ndarray = None):
    w = np.sqrt(weights) if weights is not None else np.ones_like(x)
    A = np.vstack([x, np.ones_like(x)]).T
    coef, _, _, _ = np.linalg.lstsq(A * w[:, None], y * w, rcond=None)
    return lambda x: _linear(x, *coef), coef


@register("curve_model_back", CurveModel.FOUR_PL)
def back_4pl(y: np.ndarray, params: np.ndarray) -> np.ndarray:
    return _inv_4pl(y, *params)


@register("curve_model_back", CurveModel.FIVE_PL)
def back_5pl(y: np.ndarray, params: np.ndarray) -> np.ndarray:
    return _inv_5pl(y, *params)


@register("curve_model_back", CurveModel.LINEAR)
def back_linear(y: np.ndarray, coef: np.ndarray) -> np.ndarray:
    return _inv_linear(y, *coef)
