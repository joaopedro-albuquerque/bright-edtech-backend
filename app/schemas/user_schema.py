from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UsuarioBase(BaseModel):
    email: EmailStr  
    nome: str | None = None
    estilo_preferido: str | None = None
    formato_preferido: str | None = None
    objetivos_estudo: str | None = None


class Usuario(UsuarioBase):
    id: UUID
    criado_em: datetime
    atualizado_em: datetime

    # Configuração do Pydantic v2 para garantir compatibilidade de mapeamento
    model_config = {
        "from_attributes": True
    }