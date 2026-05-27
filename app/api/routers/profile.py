from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.api.dependencies import get_profile_repo
from app.repositories.ProfileRepository import ProfileRepository
from app.schemas.user_schema import Usuario, UsuarioBase

router = APIRouter(prefix="/profile", tags=["profile"])

@router.post("/", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: UsuarioBase, repo: ProfileRepository = Depends(get_profile_repo)) -> Usuario:
    return repo.criar_usuario(usuario)

@router.get("/{user_id}", response_model=Usuario)
def buscar_usuario_por_id(user_id: UUID, repo: ProfileRepository = Depends(get_profile_repo)) -> Usuario:
    usuario = repo.buscar_usuario_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario

@router.put("/{user_id}", response_model=Usuario)
def atualizar_usuario_por_id(user_id: UUID, usuario: UsuarioBase, repo: ProfileRepository = Depends(get_profile_repo)) -> Usuario:
    usuario_atualizado = repo.atualizar_usuario_por_id(user_id, usuario)
    if not usuario_atualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario_atualizado

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_usuario_por_id(user_id: UUID, repo: ProfileRepository = Depends(get_profile_repo)) -> None:
    deleted = repo.deletar_usuario_por_id(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return None