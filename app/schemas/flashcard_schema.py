from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FlashcardCreateRequest(BaseModel):
    quantidade: int = Field(10, ge=1, le=50)


class FlashcardResponse(BaseModel):
    id: UUID
    documento_id: UUID | None = None
    titulo: str
    s3_chave: str
    tokens_utilizados: int
    modelo_ia: str | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}
