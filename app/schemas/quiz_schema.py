from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class QuizCreateRequest(BaseModel):
    quantidade: int = Field(10, ge=1, le=50)


class QuizResponse(BaseModel):
    id: UUID
    documento_id: UUID | None = None
    titulo: str
    s3_chave: str
    tokens_utilizados: int
    modelo_ia: str | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}


class QuestaoConteudoItem(BaseModel):
    id: UUID
    item_ref: str
    fator_facilidade: float
    intervalo_atual: int
    repeticoes: int
    proxima_revisao: datetime
    conteudo: dict[str, Any] | None = None


class QuizConteudoResponse(BaseModel):
    id: UUID
    titulo: str
    questoes: list[QuestaoConteudoItem]
