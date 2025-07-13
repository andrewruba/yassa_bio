from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Any, Dict, List, Tuple
import pandas as pd

from .formatting import CellFormat


class Artifact(BaseModel):
    """
    Renderable unit of output — a table, plot, text, or custom component.
    """

    kind: Literal["table", "plot", "text", "custom"] = Field(
        description="The type of artifact for rendering."
    )
    name: str = Field(description="Human-readable name, used in display headers.")
    id: str = Field(description="Unique identifier for referencing and linking.")
    data: Any = Field(
        description=(
            "The main content "
            "— e.g., DataFrame, matplotlib figure, markdown string, etc."
        ),
    )

    caption: Optional[str] = Field(description="Caption text under the artifact.")
    header: Optional[str] = Field(
        description="Text above the artifact, typically section-level heading."
    )
    footnote: Optional[str] = Field(
        description="Footnote or disclaimer text below the artifact."
    )
    show: bool = Field(
        default=True, description="Whether this artifact should be rendered."
    )

    format: Optional[str] = Field(
        default=None,
        description="Preferred output format (e.g., 'html', 'pdf', 'markdown').",
    )

    column_labels: Optional[Dict[str, str]] = Field(
        default=None,
        description="Mapping of column name → display label.",
        examples=[{"conc": "Concentration (ng/mL)"}],
    )
    column_visibility: Optional[Dict[str, bool]] = Field(
        default=None, description="Mapping of column name → visibility flag."
    )
    column_digits: Optional[Dict[str, int]] = Field(
        default=None, description="Mapping of column name → number of display digits."
    )
    cell_formats: Optional[Dict[Tuple[int, str], CellFormat]] = Field(
        default=None,
        description=(
            "Optional per-cell formatting rules keyed by (row index, column name)."
        ),
    )
    merge_identical_rows: bool = Field(
        default=False,
        description="Whether to merge identical values across consecutive rows.",
    )
    merge_columns: Optional[List[str]] = Field(
        default=None,
        description="List of columns that should be considered for row merging.",
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Arbitrary tags for grouping, filtering, or annotating artifacts.",
    )

    @field_validator("data")
    @classmethod
    def validate_data_type(cls, v, info):
        if info.data.get("kind") == "table" and not isinstance(v, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame for kind='table'")
        return v


class ArtifactGroup(BaseModel):
    """
    A logical grouping of artifacts or other groups — e.g., sections, chapters.
    """

    title: str = Field(description="Group title for rendering or navigation.")
    description: Optional[str] = Field(
        default=None, description="Optional human-readable description of this group."
    )
    order: Optional[int] = Field(
        default=None, description="Render order relative to sibling groups."
    )
    show: bool = Field(
        default=True, description="Whether this group should be rendered at all."
    )

    contents: List["ArtifactGroup" | Artifact] = Field(
        default_factory=list, description="List of artifacts or nested groups."
    )

    def flatten(self) -> List[Artifact]:
        flat: List[Artifact] = []
        for item in self.contents:
            if isinstance(item, Artifact):
                flat.append(item)
            elif isinstance(item, ArtifactGroup):
                flat.extend(item.flatten())
        return flat


ArtifactGroup.model_rebuild()
