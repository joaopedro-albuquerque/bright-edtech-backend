from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class FormatoResumoEnum(str, Enum):
    resumo_executivo = "resumo_executivo"
    cornell = "cornell"
    fichamento_academico = "fichamento_academico"


class ResumoCreateRequest(BaseModel):
    nivel_conhecimento: int = Field(..., ge=0, le=10)
    formato: FormatoResumoEnum
    tom: str


class ResumoResponse(BaseModel):
    id: UUID
    documento_id: UUID
    titulo: str
    formato: FormatoResumoEnum
    nivel_conhecimento: int
    tom: str
    s3_chave: str
    tokens_utilizados: int
    modelo_ia: str | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}


class ResumoConteudoResponse(BaseModel):
    id: UUID
    titulo: str
    conteudo: str
