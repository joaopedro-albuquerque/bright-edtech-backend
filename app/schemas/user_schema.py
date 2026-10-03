from enum import Enum

from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class EstiloPreferidoEnum(str, Enum):
    direta = "direta"
    detalhada = "detalhada"
    brincalhona = "brincalhona"


class FormatoPreferidoEnum(str, Enum):
    resumo_executivo = "resumo_executivo"
    cornell = "cornell"
    fichamento_academico = "fichamento_academico"


class OnboardingRequest(BaseModel):
    estilo_preferido: EstiloPreferidoEnum | None = None
    formato_preferido: FormatoPreferidoEnum | None = None
    objetivos_estudo: str | None = None


class UsuarioBase(BaseModel):
    email: EmailStr
    nome: str | None = None
    estilo_preferido: str | None = None
    formato_preferido: str | None = None
    objetivos_estudo: str | None = None
    cognito_id: str | None = None
    termos_versao: str | None = None
    """Versão do Termo de Uso/Consentimento LGPD aceita no cadastro (ver
    app/core/constants.py::TERMOS_DE_USO_VERSAO). Só é exigido na criação
    (POST /profile); ignorado em edições (PUT /profile/{id})."""
    tour_concluido: bool | None = None
    """Se None em um PUT, o valor atual no banco é preservado (ver
    ProfileRepository.atualizar_usuario_por_id) -- só sobrescreve quando
    o cliente manda True/False explicitamente."""

class Usuario(UsuarioBase):
    id: UUID
    termos_aceitos_em: datetime | None = None
    criado_em: datetime
    atualizado_em: datetime

    model_config = {
        "from_attributes": True
    }


class PastaBase(BaseModel):
    nome: str
    usuario_id: UUID
    pasta_pai_id: UUID | None = None


class PastaCreateRequest(BaseModel):
    """Corpo do POST /pastas: usuario_id vem do token (Depends(get_current_user_id)), não do cliente."""
    nome: str
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