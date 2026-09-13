import os
import logging
from uuid import UUID
from app.schemas.user_schema import PastaBase
from app.repositories.DocumentRepository import DocumentRepository
from app.services.S3Service import S3Service

logger = logging.getLogger(__name__)

class DocumentGeneratorService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        s3_service: S3Service | None = None,
    ):
        self.document_repo = document_repo
        self.s3_service = s3_service or S3Service()
        logger.info("DocumentGeneratorService inicializado com sucesso.")

    def criar_pasta_service(self, pasta: PastaBase) -> dict:
        logger.info(f"Iniciando criação de pasta. Dados: {pasta}")
        try:
            resultado = self.document_repo.criar_pasta(pasta)
            logger.info(f"Pasta criada com sucesso. ID: {resultado.get('id')}")
            return resultado
        except Exception as e:
            logger.error(f"Erro capturado ao criar pasta: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível criar a pasta no momento.")

    def salvar_documento(self, documento, pasta_id: UUID, usuario_id: UUID, nome_documento: str) -> dict:
        logger.info(f"Iniciando salvamento do documento '{nome_documento}' (Usuário: {usuario_id}, Pasta: {pasta_id}).")
        file_ext = os.path.splitext(documento.filename)[1]
        logger.debug(f"Extensão do arquivo identificada: {file_ext}")

        try:
            logger.info("Criando registro inicial do documento no banco...")
            documento_salvo = self.document_repo.criar_documento(
                usuario_id=usuario_id,
                pasta_id=pasta_id,
                nome=nome_documento,
                file_ext=file_ext,
                nivel_conhecimento="iniciante"
            )

            documento_id = str(documento_salvo["id"])
            chave_s3 = self.s3_service.build_document_key(usuario_id, documento_id, file_ext)
            
            logger.info(f"Fazendo upload para o S3. Chave: {chave_s3}")
            self.s3_service.upload_file(documento.file, chave_s3)

            logger.info("Atualizando chave S3 no banco de dados...")
            documento_atualizado = self.document_repo.atualizar_chave_s3(documento_id, chave_s3)

            logger.info(f"Documento {documento_id} salvo e vinculado com sucesso.")
            return {
                "id": documento_atualizado["id"],
                "nome_documento": nome_documento,
                "s3_url": f"s3://{self.s3_service.bucket_name}/{chave_s3}",
                "status": documento_atualizado.get("status"),
                "resumo": documento_atualizado.get("resumo"),
                "chave_s3": documento_atualizado.get("chave_s3"),
                "documento": documento_atualizado,
            }
        except Exception as e:
            logger.error(f"Falha na esteira de salvamento do documento '{nome_documento}': {str(e)}", exc_info=True)
            raise RuntimeError("Ocorreu um erro ao salvar o documento ou enviá-lo para a nuvem.")

    def gerar_pre_signed_url_visualizacao(self, documento_id: UUID, usuario_id: UUID) -> str:
        logger.info(f"Solicitando Pre-Signed URL. Doc: {documento_id} | User: {usuario_id}")
        try:
            documento = self.document_repo.buscar_chave_s3_por_documento_id_e_usuario(
                documento_id,
                usuario_id,
            )

            if not documento or not documento.get("chave_s3"):
                logger.warning(f"Documento não encontrado ou sem permissão. Doc ID: {documento_id}")
                raise ValueError("Documento não encontrado ou não pertence ao usuário.")

            logger.info("Gerando URL assinada no S3...")
            return self.s3_service.generate_presigned_url(documento["chave_s3"])
        except ValueError as ve:
            raise ve
        except Exception as e:
            logger.error(f"Erro ao gerar Pre-Signed URL para Doc {documento_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Falha ao gerar link de visualização do documento.")

    def listar_pastas_raiz_por_usuario(self, usuario_id: UUID, limit: int, offset: int) -> list:
        logger.info(f"Listando pastas raiz para usuário {usuario_id}.")
        try:
            return self.document_repo.listar_pastas_raiz_por_usuario(usuario_id, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar pastas raiz do usuário {usuario_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível carregar as pastas.")

    def listar_todas_pastas_por_usuario(self, usuario_id: UUID) -> list:
        logger.info(f"Listando todas as pastas para o usuário {usuario_id}.")
        try:
            return self.document_repo.listar_todas_pastas_por_usuario(usuario_id)
        except Exception as e:
            logger.error(f"Erro ao listar todas as pastas do usuário {usuario_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível carregar a estrutura de pastas.")
    
    def listar_conteudo_pasta(self, pasta_id: UUID, limit: int, offset: int) -> dict:
        logger.info(f"Listando conteúdo da pasta {pasta_id}.")
        try:
            return self.document_repo.listar_conteudo_pasta(pasta_id, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar conteúdo da pasta {pasta_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível carregar o conteúdo da pasta.")

    def atualizar_pasta_nome(self, pasta_id: UUID, nome: str) -> dict | None:
        logger.info(f"Atualizando nome da pasta {pasta_id} para '{nome}'.")
        try:
            resultado = self.document_repo.atualizar_pasta_nome(pasta_id, nome)
            if not resultado:
                logger.warning(f"Pasta {pasta_id} não encontrada para atualização.")
            else:
                logger.info(f"Pasta {pasta_id} renomeada com sucesso.")
            return resultado
        except Exception as e:
            logger.error(f"Erro ao renomear pasta {pasta_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível renomear a pasta.")

    def atualizar_documento_nome(self, documento_id: UUID, nome: str) -> dict | None:
        logger.info(f"Atualizando nome do documento {documento_id} para '{nome}'.")
        try:
            resultado = self.document_repo.atualizar_documento_nome(documento_id, nome)
            if not resultado:
                logger.warning(f"Documento {documento_id} não encontrado para atualização.")
            else:
                logger.info(f"Documento {documento_id} renomeado com sucesso.")
            return resultado
        except Exception as e:
            logger.error(f"Erro ao renomear documento {documento_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível renomear o documento.")

    def deletar_documento(self, documento_id: UUID, usuario_id: UUID) -> bool:
        logger.warning(f"Solicitação de exclusão para o documento {documento_id}.")
        try:
            resultado = self.document_repo.deletar_documento(documento_id, usuario_id)
            if resultado:
                logger.info(f"Documento {documento_id} deletado com sucesso.")
            else:
                logger.warning(f"Documento {documento_id} não encontrado ou já deletado.")
            return resultado
        except Exception as e:
            logger.error(f"Erro ao deletar documento {documento_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível excluir o documento.")

    def deletar_pasta(self, pasta_id: UUID) -> bool:
        logger.warning(f"Solicitação de exclusão para a pasta {pasta_id}.")
        try:
            resultado = self.document_repo.deletar_pasta(pasta_id)
            if resultado:
                logger.info(f"Pasta {pasta_id} deletada com sucesso.")
            else:
                logger.warning(f"Pasta {pasta_id} não encontrada ou já deletada.")
            return resultado
        except Exception as e:
            logger.error(f"Erro ao deletar pasta {pasta_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível excluir a pasta. Verifique se ela está vazia.")