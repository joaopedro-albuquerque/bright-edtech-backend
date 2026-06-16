from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UsuarioBase(BaseModel):
    email: EmailStr  
    nome: str | None = None
    estilo_preferido: str | None = None
    formato_preferido: str | None = None
    objetivos_estudo: str | None = None
    cognito_id: str | None = None

class Usuario(UsuarioBase):
    id: UUID
    criado_em: datetime
    atualizado_em: datetime

    model_config = {
        "from_attributes": True
    }


class PastaBase(BaseModel):
    nome: str
    usuario_id: UUID
    pasta_pai_id: UUID | None = None


class Pasta(PastaBase):
    id: UUID
    criada_em: datetime

    model_config = {
        "from_attributes": True
    }

class PastaListagemResponse(BaseModel):
    id: UUID
    nome: str
    criada_em: datetime

    model_config = {"from_attributes": True}

class SubpastaResponse(BaseModel):
    id: UUID
    nome: str
    criada_em: datetime | None = None

class DocumentoResponse(BaseModel):
    id: UUID
    nome: str
    status: str
    resumo: str | None = None

class PastaConteudoResponse(BaseModel):
    subpastas: list[SubpastaResponse]
    arquivos: list[DocumentoResponse]
    total_arquivos: int
    pagina_atual: int
    tem_mais_paginas: bool