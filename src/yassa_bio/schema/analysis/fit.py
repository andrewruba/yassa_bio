from __future__ import annotations
from pydantic import Field

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.analysis.enum import (
    CurveModel,
    Weighting,
    Transformation,
)
from yassa_bio.core.enum import enum_examples


class CurveFit(SchemaModel):
    """
    Parameters defining the mathematical model used for fitting the
     calibration standard curve.
    """

    model: CurveModel = Field(
        CurveModel.FOUR_PL,
        description="Mathematical model used to fit the calibration standard curve.",
        examples=enum_examples(CurveModel),
    )
    transformation_x: Transformation = Field(
        Transformation.IDENTITY,
        description="Transformation applied to x-values prior to fitting.",
        examples=enum_examples(Transformation),
    )
    transformation_y: Transformation = Field(
        Transformation.IDENTITY,
        description="Transformation applied to y-values prior to fitting.",
        examples=enum_examples(Transformation),
    )
    weighting: Weighting = Field(
        Weighting.ONE,
        description="Weighting scheme applied to curve fit residuals.",
        examples=enum_examples(Weighting),
    )
