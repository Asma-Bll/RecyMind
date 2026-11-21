
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


TypeDechet = Literal[
    "plastique",
    "papier_carton",
    "verre",
    "metal",
    "textile",
    "autre",
]

StatutTri = Literal["trie", "controle_manuel"]


class TriCreate(BaseModel):
    date: datetime
    image_url: str = Field(min_length=1, max_length=1000)
    type: Literal[
        "plastique",
        "papier_carton",
        "verre",
        "metal",
        "textile",
        "autre",
        "tapis_vide",
    ]
    confiance: float = Field(ge=0, le=1)


class CorrectionRead(BaseModel):
    type_corrige: TypeDechet
    date_correction: datetime

    model_config = ConfigDict(from_attributes=True)


class TriRead(BaseModel):
    id: UUID
    date: datetime
    image_url: str
    type: TypeDechet
    confiance: float
    bac: str | None
    statut: StatutTri
    correction: CorrectionRead | None = None

    model_config = ConfigDict(from_attributes=True)


class TriListRead(BaseModel):
    items: list[TriRead]
    page: int
    limit: int
    total: int


class ActionResponse(BaseModel):
    action: str
    message: str
