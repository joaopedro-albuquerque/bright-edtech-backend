import os
import logging
from uuid import UUID

from app.core.exceptions import (
    AiGenerationError,
    ConteudoImproprioError,
    DocumentNotFoundError,
    ModeracaoIndisponivelError,
    NotificationContext,
)
from app.repositories.DocumentRepository import DocumentRepository
from app.services.BedrockService import BedrockService
from app.services.S3Service import S3Service
from app.services.pdf_utils import amostrar_paginas, contar_paginas

logger = logging.getLogger(__name__)

TAMANHO_MAXIMO_PDF_BYTES = 5 * 1024 * 1024
MAXIMO_PAGINAS_PDF = 100
CONTENT_TYPES_PDF_VALIDOS = {"application/pdf"}


class DocumentGeneratorService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        s3_service: S3Service | None = None,
        bedrock_service: BedrockService | None = None,
    ):
        self.document_repo = document_repo
        self.s3_service = s3_service or S3Service()
        self.bedrock_service = bedrock_service or BedrockService()
        logger.info("DocumentGeneratorService inicializado com sucesso.")

    def criar_pasta_service(self, usuario_id: UUID, nome: str, pasta_pai_id: UUID | None) -> dict:
        logger.info(f"Iniciando criação de pasta '{nome}' para o usuário {usuario_id}.")
        resultado = self.document_repo.criar_pasta(usuario_id, nome, pasta_pai_id)
        logger.info(f"Pasta criada com sucesso. ID: {resultado.get('id')}")
        return resultado

    def _validar_arquivo_pdf(self, documento, file_ext: str) -> None:
        ctx = NotificationContext()

        if file_ext.lower() != ".pdf" or documento.content_type not in CONTENT_TYPES_PDF_VALIDOS:
            ctx.add(1003, "documento", "Apenas arquivos no formato PDF são permitidos.")

        if documento.size is not None and documento.size > TAMANHO_MAXIMO_PDF_BYTES:
            ctx.add(1004, "documento", "O arquivo excede o tamanho máximo permitido de 5MB.")

        ctx.raise_if_any()

    def _moderar_documento(self, documento) -> None:
        """Bloqueia PDFs ilegíveis, longos demais e conteúdo sexual. Falha fechada: se a IA não responder, o upload é recusado."""
        try:
            total_paginas = contar_paginas(documento.file)
        except ValueError:
            total_paginas = 0

        if total_paginas == 0:
            ctx = NotificationContext()
            ctx.add(1006, "documento", "O arquivo PDF está corrompido ou é ilegível.")
            ctx.raise_if_any()

        if total_paginas > MAXIMO_PAGINAS_PDF:
            ctx = NotificationContext()
            ctx.add(1008, "documento", f"O PDF excede o limite de {MAXIMO_PAGINAS_PDF} páginas.")
            ctx.raise_if_any()

        try:
            amostra_pdf = amostrar_paginas(documento.file)
        except ValueError:
            ctx = NotificationContext()
            ctx.add(1006, "documento", "O arquivo PDF está corrompido ou é ilegível.")
            ctx.raise_if_any()

        try:
            improprio, motivo = self.bedrock_service.moderar_conteudo(amostra_pdf)
        except AiGenerationError as exc:
            logger.error(f"Moderação de conteúdo indisponível, upload bloqueado: {exc}")
            raise ModeracaoIndisponivelError() from exc

        if improprio:
            logger.warning(f"Upload recusado pela moderação de conteúdo. Motivo: {motivo}")
            raise ConteudoImproprioError()

    def salvar_documento(self, documento, pasta_id: UUID, usuario_id: UUID, nome_documento: str) -> dict:
        logger.info(f"Iniciando salvamento do documento '{nome_documento}' (Usuário: {usuario_id}, Pasta: {pasta_id}).")
        file_ext = os.path.splitext(documento.filename)[1]
        logger.debug(f"Extensão do arquivo identificada: {file_ext}")

        self._validar_arquivo_pdf(documento, file_ext)
        self._moderar_documento(documento)

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

    def gerar_pre_signed_url_visualizacao(self, documento_id: UUID, usuario_id: UUID) -> str:
        logger.info(f"Solicitando Pre-Signed URL. Doc: {documento_id} | User: {usuario_id}")
        documento = self.document_repo.buscar_chave_s3_por_documento_id_e_usuario(
            documento_id,
            usuario_id,
        )

        if not documento or not documento.get("chave_s3"):
            logger.warning(f"Documento não encontrado ou sem permissão. Doc ID: {documento_id}")
            raise DocumentNotFoundError("Documento não encontrado ou não pertence ao usuário.")

        logger.info("Gerando URL assinada no S3...")
        return self.s3_service.generate_presigned_url(documento["chave_s3"])

    def listar_pastas_raiz_por_usuario(self, usuario_id: UUID, limit: int, offset: int) -> list:
        logger.info(f"Listando pastas raiz para usuário {usuario_id}.")
        return self.document_repo.listar_pastas_raiz_por_usuario(usuario_id, limit, offset)

    def listar_todas_pastas_por_usuario(self, usuario_id: UUID) -> list:
        logger.info(f"Listando todas as pastas para o usuário {usuario_id}.")
        return self.document_repo.listar_todas_pastas_por_usuario(usuario_id)

    def listar_conteudo_pasta(self, pasta_id: UUID, usuario_id: UUID, limit: int, offset: int) -> dict:
        logger.info(f"Listando conteúdo da pasta {pasta_id}.")
        conteudo = self.document_repo.listar_conteudo_pasta(pasta_id, usuario_id, limit, offset)
        if conteudo is None:
            raise DocumentNotFoundError("Pasta não encontrada.")
        return conteudo

    def atualizar_pasta_nome(self, pasta_id: UUID, nome: str, usuario_id: UUID) -> dict:
        logger.info(f"Atualizando nome da pasta {pasta_id} para '{nome}'.")
        resultado = self.document_repo.atualizar_pasta_nome(pasta_id, nome, usuario_id)
        if not resultado:
            logger.warning(f"Pasta {pasta_id} não encontrada para atualização.")
            raise DocumentNotFoundError("Pasta não encontrada.")
        logger.info(f"Pasta {pasta_id} renomeada com sucesso.")
        return resultado

    def atualizar_documento_nome(self, documento_id: UUID, nome: str, usuario_id: UUID) -> dict:
        logger.info(f"Atualizando nome do documento {documento_id} para '{nome}'.")
        resultado = self.document_repo.atualizar_documento_nome(documento_id, nome, usuario_id)
        if not resultado:
            logger.warning(f"Documento {documento_id} não encontrado para atualização.")
            raise DocumentNotFoundError("Documento não encontrado.")
        logger.info(f"Documento {documento_id} renomeado com sucesso.")
        return resultado

    def deletar_documento(self, documento_id: UUID, usuario_id: UUID) -> None:
        logger.warning(f"Solicitação de exclusão para o documento {documento_id}.")
        # Arquivos primeiro: se falhar, nada é apagado e o usuário pode tentar de novo.
        self.s3_service.delete_prefix(self.s3_service.build_document_prefix(str(usuario_id), str(documento_id)))
        resultado = self.document_repo.deletar_documento(documento_id, usuario_id)
        if not resultado:
            logger.warning(f"Documento {documento_id} não encontrado ou já deletado.")
            raise DocumentNotFoundError("Documento não encontrado.")
        logger.info(f"Documento {documento_id} deletado com sucesso.")

    def deletar_pasta(self, pasta_id: UUID, usuario_id: UUID) -> None:
        logger.warning(f"Solicitação de exclusão para a pasta {pasta_id}.")
        resultado = self.document_repo.deletar_pasta(pasta_id, usuario_id)
        if not resultado:
            logger.warning(f"Pasta {pasta_id} não encontrada ou já deletada.")
            raise DocumentNotFoundError("Pasta não encontrada.")
        logger.info(f"Pasta {pasta_id} deletada com sucesso.")
