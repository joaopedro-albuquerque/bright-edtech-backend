import logging
from uuid import UUID

from app.core.config import TERMOS_DE_USO_VERSAO
from app.core.exceptions import NotificationContext, ProfileNotFoundError
from app.repositories.ProfileRepository import ProfileRepository
from app.schemas.user_schema import (
    EstiloPreferidoEnum,
    FormatoPreferidoEnum,
    OnboardingRequest,
    Usuario,
    UsuarioBase,
)

logger = logging.getLogger(__name__)

class ProfileService:
    def __init__(self, repo: ProfileRepository):
        self.repo = repo
        logger.info("ProfileService inicializado com sucesso.")

    def _validar_usuario_base(self, usuario: UsuarioBase, exigir_termos: bool) -> None:
        ctx = NotificationContext()
        estilos_validos = {e.value for e in EstiloPreferidoEnum}
        formatos_validos = {f.value for f in FormatoPreferidoEnum}

        if usuario.estilo_preferido and usuario.estilo_preferido not in estilos_validos:
            ctx.add(2101, "estilo_preferido", "Estilo de estudo preferido inválido.")

        if usuario.formato_preferido and usuario.formato_preferido not in formatos_validos:
            ctx.add(2102, "formato_preferido", "Formato preferido inválido.")

        if exigir_termos and usuario.termos_versao != TERMOS_DE_USO_VERSAO:
            ctx.add(
                2103,
                "termos_versao",
                "É necessário aceitar a versão vigente dos Termos de Uso e da Política de Privacidade.",
            )

        ctx.raise_if_any()

    def criar_usuario(self, usuario: UsuarioBase) -> Usuario:
        logger.info(f"Iniciando criação de perfil para o email: {usuario.email}")
        self._validar_usuario_base(usuario, exigir_termos=True)
        novo_usuario = self.repo.criar_usuario(usuario)
        logger.info(f"Usuário criado com sucesso. ID gerado: {novo_usuario.id}")
        return novo_usuario

    def buscar_usuario_por_id(self, user_id: UUID) -> Usuario:
        logger.info(f"Buscando perfil do usuário ID: {user_id}")
        usuario = self.repo.buscar_usuario_por_id(user_id)
        if not usuario:
            logger.warning(f"Usuário não encontrado na base de dados. ID: {user_id}")
            raise ProfileNotFoundError(f"Usuário {user_id} não encontrado.")
        logger.debug(f"Usuário {user_id} encontrado e dados recuperados com sucesso.")
        return usuario

    def atualizar_usuario_por_id(self, user_id: UUID, usuario: UsuarioBase) -> Usuario:
        logger.info(f"Iniciando atualização de dados para o usuário ID: {user_id}")
        self._validar_usuario_base(usuario, exigir_termos=False)
        usuario_atualizado = self.repo.atualizar_usuario_por_id(user_id, usuario)
        if not usuario_atualizado:
            logger.warning(f"Falha na atualização: Usuário {user_id} não existe na base.")
            raise ProfileNotFoundError(f"Usuário {user_id} não encontrado.")
        logger.info(f"Perfil do usuário {user_id} atualizado com sucesso.")
        return usuario_atualizado

    def atualizar_perfil_onboarding(self, user_id: UUID, perfil: OnboardingRequest) -> Usuario:
        logger.info(f"Salvando respostas de onboarding para o usuário ID: {user_id}")
        usuario_atualizado = self.repo.atualizar_perfil_onboarding(user_id, perfil)
        if not usuario_atualizado:
            logger.warning(f"Falha no onboarding: Usuário {user_id} não existe na base.")
            raise ProfileNotFoundError(f"Usuário {user_id} não encontrado.")
        logger.info(f"Onboarding do usuário {user_id} salvo com sucesso.")
        return usuario_atualizado

    def deletar_usuario_por_id(self, user_id: UUID) -> None:
        logger.warning(f"Solicitação de exclusão permanente recebida para o usuário ID: {user_id}")
        sucesso = self.repo.deletar_usuario_por_id(user_id)
        if not sucesso:
            logger.error(f"A exclusão falhou: Usuário {user_id} não foi encontrado ou já havia sido removido.")
            raise ProfileNotFoundError(f"Usuário {user_id} não encontrado.")
        logger.info(f"Perfil do usuário {user_id} deletado com sucesso do banco de dados.")

    def buscar_usuario_por_cognito_id(self, cognito_id: str) -> Usuario:
        logger.info(f"Buscando perfil do usuário pelo Cognito ID: {cognito_id}")
        usuario = self.repo.buscar_usuario_por_cognito_id(cognito_id)
        if not usuario:
            logger.warning(f"Usuário com Cognito ID {cognito_id} não existe na base de dados.")
            raise ProfileNotFoundError("Usuário não encontrado.")
        logger.debug("Usuário localizado com sucesso via Cognito ID.")
        return usuario
