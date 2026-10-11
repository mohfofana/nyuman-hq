from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

from domain.entities.objectif import Objectif, SuiviObjectif
from use_cases.core.objectif.save_current_objectif_use_case import ObjectifInput

PoleParam = Literal["direction", "operations", "produit", "croissance", ""]


class ObjectifViewModel(BaseModel):
    id: int
    title: str
    quarter: str
    metric: str
    target: float
    start_date: date
    end_date: date
    pole: str
    current: Optional[float]
    progress: Optional[float]
    weeks_left: int
    needed_per_week: Optional[float]

    @classmethod
    def of(cls, objectif: Objectif, suivi: SuiviObjectif) -> "ObjectifViewModel":
        return cls(
            id=objectif.id,
            title=objectif.title,
            quarter=objectif.quarter,
            metric=objectif.metric,
            target=objectif.target,
            start_date=objectif.start_date,
            end_date=objectif.end_date,
            pole=objectif.pole,
            current=suivi.current,
            progress=suivi.progress,
            weeks_left=suivi.weeks_left,
            needed_per_week=suivi.needed_per_week,
        )


class SaveObjectifRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    quarter: str = Field(min_length=1, max_length=20)
    metric: str
    target: float = Field(gt=0)
    start_date: date
    end_date: date
    current_manual: Optional[float] = Field(default=None, ge=0)

    def to_input(self) -> ObjectifInput:
        return ObjectifInput(**self.model_dump())


class AvancementRequest(BaseModel):
    value: float = Field(ge=0)
