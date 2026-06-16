import logging
from uuid import UUID

from app.repositories.ProfileRepository import ProfileRepository
from app.schemas.user_schema import Usuario, UsuarioBase

# Instancia o logger para este arquivo
logger = logging.getLogger(__name__)

class ProfileService:
    def __init__(self, repo: ProfileRepository):
        self.repo = repo
        logger.info("ProfileService inicializado com sucesso.")

    def criar_usuario(self, usuario: UsuarioBase) -> Usuario:
        logger.info(f"Iniciando criação de perfil para o email: {usuario.email}")
        try:
            novo_usuario = self.repo.criar_usuario(usuario)
            
            if not novo_usuario:
                logger.error("Repositório falhou silenciosamente ao retornar o usuário recém-criado.")
                raise RuntimeError("Erro ao criar perfil no banco de dados.")
                
            logger.info(f"Usuário criado com sucesso. ID gerado: {novo_usuario.id}")
            return novo_usuario
            
        except Exception as e:
            logger.error(f"Falha ao criar o usuário ({usuario.email}): {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível criar o perfil do usuário.")

    def buscar_usuario_por_id(self, user_id: UUID) -> Usuario | None:
        logger.info(f"Buscando perfil do usuário ID: {user_id}")
        try:
            usuario = self.repo.buscar_usuario_por_id(user_id)
            
            if not usuario:
                logger.warning(f"Usuário não encontrado na base de dados. ID: {user_id}")
            else:
                logger.debug(f"Usuário {user_id} encontrado e dados recuperados com sucesso.")
                
            return usuario
            
        except Exception as e:
            logger.error(f"Falha de banco de dados ao buscar o usuário {user_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível recuperar os dados do perfil.")

    def atualizar_usuario_por_id(self, user_id: UUID, usuario: UsuarioBase) -> Usuario | None:
        logger.info(f"Iniciando atualização de dados para o usuário ID: {user_id}")
        try:
            usuario_atualizado = self.repo.atualizar_usuario_por_id(user_id, usuario)
            
            if not usuario_atualizado:
                logger.warning(f"Falha na atualização: Usuário {user_id} não existe na base.")
            else:
                logger.info(f"Perfil do usuário {user_id} atualizado com sucesso.")
                
            return usuario_atualizado
            
        except Exception as e:
            logger.error(f"Falha ao atualizar dados do usuário {user_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível atualizar o perfil do usuário.")

    def deletar_usuario_por_id(self, user_id: UUID) -> bool:
        logger.warning(f"Solicitação de exclusão permanente recebida para o usuário ID: {user_id}")
        try:
            sucesso = self.repo.deletar_usuario_por_id(user_id)
            
            if sucesso:
                logger.info(f"Perfil do usuário {user_id} deletado com sucesso do banco de dados.")
            else:
                logger.error(f"A exclusão falhou: Usuário {user_id} não foi encontrado ou já havia sido removido.")
                
            return sucesso
            
        except Exception as e:
            logger.error(f"Falha crítica ao tentar deletar o usuário {user_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível excluir o perfil do usuário.")
        
    def buscar_usuario_por_cognito_id(self, cognito_id: str) -> Usuario | None:
        logger.info(f"Buscando perfil do usuário pelo Cognito ID: {cognito_id}")
        try:
            usuario = self.repo.buscar_usuario_por_cognito_id(cognito_id)
            
            if not usuario:
                logger.warning(f"Usuário com Cognito ID {cognito_id} não existe na base de dados.")
            else:
                logger.debug("Usuário localizado com sucesso via Cognito ID.")
                
            return usuario
            
        except Exception as e:
            logger.error(f"Falha ao buscar o usuário Cognito {cognito_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível recuperar os dados do perfil.")