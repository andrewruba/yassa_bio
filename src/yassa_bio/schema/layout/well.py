from __future__ import annotations
import re
from typing import Optional
from pydantic import Field, model_validator, field_validator

from yassa_bio.schema.layout.enum import (
    SampleType,
    QCLevel,
    StabilityConditionTime,
    RecoveryStage,
)
from yassa_bio.core.model import SchemaModel
from yassa_bio.core.enum import enum_examples


class WellTemplate(SchemaModel):
    """Map one physical well to its location in the raw data table."""

    well: str = Field(
        ...,
        description="Canonical ID (e.g. 'A1', 'H12', 'AA24').",
        examples=["A1", "H12", "AA24"],
    )
    file_row: int = Field(
        ...,
        ge=0,
        description="0-based absolute row index in the raw file.",
    )
    file_col: int = Field(
        ...,
        ge=0,
        description="0-based absolute column index in the raw file.",
    )

    sample_id: Optional[str] = Field(
        None,
        description=(
            "Logical ID of the original study sample this well belongs to. "
            "Use the same ID across all dilution levels to form a series."
        ),
        examples=["SUBJ_1234_VISIT1", "SERUM_A", "POOL42"],
    )
    sample_type: SampleType = Field(
        ...,
        description="High-level role of this well in the assay.",
        examples=[sample_type.value for sample_type in SampleType],
    )
    interferent: Optional[str] = Field(
        None,
        description=(
            "Name / ID of related, interfering molecule spiked into this well. "
            "None = no interferent."
        ),
        examples=["glucose", "cholesterol", "bovine serum albumin"],
    )
    carryover: bool = Field(
        False,
        description=(
            "Set True when this blank is intended for the post-ULOQ carry-over check."
        ),
    )
    stability_condition: Optional[str] = Field(
        None,
        description=(
            "Label of the stability experiment this QC aliquot belongs to. "
            "Leave as none if well does not participate in stability test."
        ),
        examples=["freeze-thaw", "long-term", "autosampler"],
    )
    stability_condition_time: Optional[StabilityConditionTime] = Field(
        None,
        description=(
            "Indicates if the well is before or after condition has been applied."
        ),
        examples=enum_examples(StabilityConditionTime),
    )
    recovery_stage: Optional[RecoveryStage] = Field(
        None,
        description=(
            "Marks wells used in extraction recovery experiments. "
            "Leave as None if well does not participate in recovery test."
        ),
        examples=enum_examples(RecoveryStage),
    )
    qc_level: Optional[QCLevel] = Field(
        None,
        description=(
            "QC band for quality control wells. "
            "Leave blank when the assay has only one global tolerance band."
        ),
        examples=enum_examples(QCLevel),
    )
    replicate: Optional[int] = Field(
        None,
        ge=1,
        description="1-based replicate counter inside a group; leave None if N/A.",
    )
    level_idx: Optional[int] = Field(
        None,
        ge=1,
        description="Serial-dilution position (Std-1 → 1, Std-2 → 2, …).",
    )
    concentration: Optional[float] = Field(
        None,
        description="Absolute concentration override for this individual well.",
    )
    concentration_units: Optional[str] = Field(
        None,
        description=(
            "Units for the concentration override (e.g. 'ng/mL'). "
            "Required if `concentration` is set."
        ),
        examples=["ng/mL", "pg/mL", "mU/mL", "IU/mL"],
    )

    exclude: bool = Field(
        False,
        description="Mark True to drop this well from all downstream calculations.",
    )
    exclude_reason: Optional[str] = Field(
        None,
        description=(
            "≤ 5-word reason for exclusion (e.g. 'bubble', 'edge leak'). "
            "Required if `exclude` is True."
        ),
    )

    @model_validator(mode="after")
    def _reason_required_if_excluded(self):
        if self.exclude and not self.exclude_reason:
            raise ValueError("exclude_reason must be provided whenever exclude is True")
        return self

    @model_validator(mode="after")
    def _units_required_if_concentration(self):
        if (self.concentration is not None) != (self.concentration_units is not None):
            raise ValueError(
                "'concentration' and 'concentration_units' must be provided together"
            )
        return self

    @field_validator("well", mode="before")
    @classmethod
    def _validate_well_id(cls, v: str) -> str:
        v = v.strip().upper()
        _WELL_ID_RE = re.compile(r"^[A-Z]{1,3}[1-9][0-9]*$")
        if not _WELL_ID_RE.fullmatch(v):
            raise ValueError(
                "well must match plate notation like 'A1', 'H12', 'AA24' "
                "(letters followed by a non-zero column number)"
            )
        return v

    @model_validator(mode="after")
    def _qc_level_allowed_for_type(self):
        if self.sample_type is not SampleType.QUALITY_CONTROL and self.qc_level:
            raise ValueError("qc_level only valid on QUALITY_CONTROL wells")
        return self

    @model_validator(mode="after")
    def _carryover_only_on_blank(self):
        if self.carryover and self.sample_type is not SampleType.BLANK:
            raise ValueError("carryover flag is only valid on BLANK wells")
        return self

    @model_validator(mode="after")
    def _time_requires_condition(self):
        has_cond = self.stability_condition is not None
        has_timept = self.stability_condition_time is not None

        if has_cond ^ has_timept:
            raise ValueError(
                "stability_condition and stability_condition_time must be set together"
            )
        return self

    @model_validator(mode="after")
    def _recovery_requires_qc_and_level(self):
        if self.recovery_stage:
            if self.sample_type is not SampleType.QUALITY_CONTROL:
                raise ValueError("recovery_stage allowed only on QUALITY_CONTROL wells")
            if self.qc_level is None:
                raise ValueError("recovery_stage requires qc_level to be set")
        return self

    @model_validator(mode="after")
    def _cal_std_must_resolve_conc(self):
        is_std = self.sample_type is SampleType.CALIBRATION_STANDARD
        has_lvl = self.level_idx is not None
        has_conc = self.concentration is not None

        if is_std:
            if not (has_lvl or has_conc):
                raise ValueError(
                    "CALIBRATION_STANDARD requires concentration override or level_idx"
                )
        else:
            if has_lvl:
                raise ValueError(
                    "level_idx is only valid on CALIBRATION_STANDARD wells"
                )
        return self
