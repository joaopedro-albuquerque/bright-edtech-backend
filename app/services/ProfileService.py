from uuid import UUID

from app.repositories.ProfileRepository import ProfileRepository
from app.schemas.user_schema import Usuario, UsuarioBase


class ProfileService:
    def __init__(self, repo: ProfileRepository):
        self.repo = repo

    def criar_usuario(self, usuario: UsuarioBase) -> Usuario:
        return self.repo.criar_usuario(usuario)

    def buscar_usuario_por_id(self, user_id: UUID) -> Usuario | None:
        return self.repo.buscar_usuario_por_id(user_id)

    def atualizar_usuario_por_id(self, user_id: UUID, usuario: UsuarioBase) -> Usuario | None:
        return self.repo.atualizar_usuario_por_id(user_id, usuario)

    def deletar_usuario_por_id(self, user_id: UUID) -> bool:
        return self.repo.deletar_usuario_por_id(user_id)
