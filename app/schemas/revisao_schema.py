from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AvaliarRequest(BaseModel):
    qualidade: int = Field(..., ge=1, le=5)


class ItemRevisaoResponse(BaseModel):
    id: UUID
    origem_id: UUID  # flashcard_id ou quiz_id
    item_ref: str
    fator_facilidade: float
    intervalo_atual: int
    repeticoes: int
    proxima_revisao: datetime
    conteudo: dict | None = None


class DailyMixResponse(BaseModel):
    cartoes: list[ItemRevisaoResponse]
    questoes: list[ItemRevisaoResponse]
    total: int


class AvaliarResponse(BaseModel):
    id: UUID
    fator_facilidade: float
    intervalo_atual: int
    repeticoes: int
    proxima_revisao: datetime
