from __future__ import annotations

from pydantic import (
    Field,
    PositiveFloat,
    model_validator,
)

from yassa_bio.core.model import SchemaModel
from yassa_bio.core.typing import Fraction01, Percent
from yassa_bio.schema.layout.enum import QCLevel


class DetectionRule(SchemaModel):
    """
    Rules for deriving LOD and LOQ from blank well variability.
    """

    lod_snr: float = Field(
        3.0,
        description=(
            "LOD threshold: signal must be at least this multiple of the "
            "standard deviation of blanks (SNR ≥ N)."
        ),
    )
    loq_snr: float = Field(
        10.0,
        description=(
            "LOQ threshold: signal must be at least this multiple of the "
            "standard deviation of blanks (SNR ≥ N)."
        ),
    )


class ReplicateCriteria(SchemaModel):
    """
    Constraint on the variability of replicate wells.
    """

    max_cv_percent: PositiveFloat = Percent(
        10.0, lo=1, hi=50, description="Maximum allowed CV (%) across replicate wells."
    )


class QCBand(SchemaModel):
    """
    Defines a recovery tolerance window for a specific QC band.
    """

    level: QCLevel = Field(
        QCLevel.ALL, description="QC band label this spec applies to."
    )
    min_tol_pct: PositiveFloat = Percent(
        80, lo=0, hi=200, description="Lower recovery limit (%)."
    )
    max_tol_pct: PositiveFloat = Percent(
        120, lo=0, hi=200, description="Upper recovery limit (%)."
    )

    @model_validator(mode="after")
    def _check_window(self):
        if self.min_tol_pct >= self.max_tol_pct:
            raise ValueError("min_tol_pct must be < max_tol_pct")
        return self


class LinearityRules(SchemaModel):
    """
    Rules for validating the linearity of the calibration curve.
    """

    r_squared_min: PositiveFloat = Fraction01(
        0.98, description="Minimum acceptable R² for the linearity fit."
    )
    per_level_acc_pct: PositiveFloat = Percent(
        15.0, lo=5, hi=50, description="Accuracy threshold (%) required at each level."
    )
    min_levels_pass: PositiveFloat = Fraction01(
        0.75, description="Fraction of levels that must pass accuracy check."
    )


class DilutionLinearity(SchemaModel):
    """
    Requirements for evaluating sample dilution performance.
    """

    max_bias_pct: PositiveFloat = Percent(
        20.0, lo=5, hi=50, description="Maximum allowed bias (%) after dilution."
    )
    max_cv_pct: PositiveFloat = Percent(
        20.0,
        lo=5,
        hi=50,
        description="Maximum allowed CV (%) across dilution replicates.",
    )
    min_levels: int = Field(
        3, ge=3, le=8, description="Minimum number of dilution levels to evaluate."
    )
    series_required: int = Field(
        3, ge=1, le=10, description="Number of replicate dilution series required."
    )


class HookEffectCheck(SchemaModel):
    """
    Checks for potential hook effect (signal suppression at high concentration).
    Validates that the undiluted sample's signal meets a minimum percentage
    of its own diluted versions to rule out nonlinear suppression.
    """

    threshold_pct_of_undiluted: PositiveFloat = Percent(
        80.0,
        lo=50,
        hi=100,
        description="Minimum response (%) of undiluted sample required to pass.",
    )


class TotalErrorRule(SchemaModel):
    """
    Limits on combined bias and variability for quantifiable samples.
    Used for evaluating overall performance and accuracy of the assay.
    """

    overall_pct: PositiveFloat = Percent(
        30.0,
        lo=5,
        hi=100,
        description="Total error threshold (%) for all quantifiable samples.",
    )
    loq_pct: PositiveFloat = Percent(
        40.0, lo=5, hi=100, description="Total error threshold (%) specifically at LOQ."
    )


class QCSpec(SchemaModel):
    """
    Aggregate quality control specification for the assay.
    """

    duplicate_cv: ReplicateCriteria = ReplicateCriteria()
    bands: list[QCBand] = [QCBand()]
    linearity: LinearityRules = LinearityRules()
    dilution: DilutionLinearity = DilutionLinearity()
    hook: HookEffectCheck = HookEffectCheck()
    total_error: TotalErrorRule = TotalErrorRule()
    detection_rule: DetectionRule = DetectionRule()
