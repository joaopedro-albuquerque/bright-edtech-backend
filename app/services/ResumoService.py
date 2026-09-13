import logging
from uuid import UUID

from app.repositories.DocumentRepository import DocumentRepository
from app.repositories.ResumoRepository import ResumoRepository
from app.services.BedrockService import BedrockService
from app.services.S3Service import S3Service
from app.services.pdf_utils import extrair_texto_do_pdf

logger = logging.getLogger(__name__)


class ResumoService:
    def __init__(
        self,
        resumo_repo: ResumoRepository,
        document_repo: DocumentRepository,
        s3_service: S3Service | None = None,
        bedrock_service: BedrockService | None = None,
    ):
        self.resumo_repo = resumo_repo
        self.document_repo = document_repo
        self.s3_service = s3_service or S3Service()
        self.bedrock_service = bedrock_service or BedrockService()

    def gerar_resumo(
        self, documento_id: UUID, usuario_id: UUID, nivel_conhecimento: int, formato: str, tom: str
    ) -> dict:
        logger.info(f"Gerando resumo (formato={formato}) para documento {documento_id}.")

        documento = self.document_repo.buscar_chave_s3_por_documento_id_e_usuario(documento_id, usuario_id)
        if not documento or not documento.get("chave_s3"):
            raise ValueError("Documento não encontrado ou não pertence ao usuário.")

        arquivo_pdf = self.s3_service.download_file(documento["chave_s3"])
        texto_extraido = extrair_texto_do_pdf(arquivo_pdf)

        texto_gerado, tokens_utilizados, modelo_ia = self.bedrock_service.gerar_resumo(
            texto_extraido, formato, nivel_conhecimento, tom
        )

        titulo = f"Resumo ({formato})"
        s3_chave = f"artifacts/{usuario_id}/{documento_id}/resumo-{formato}.md"
        self.s3_service.upload_text(texto_gerado, s3_chave)

        return self.resumo_repo.criar(
            documento_id=documento_id,
            usuario_id=usuario_id,
            titulo=titulo,
            formato=formato,
            nivel_conhecimento=nivel_conhecimento,
            tom=tom,
            s3_chave=s3_chave,
            tokens_utilizados=tokens_utilizados,
            modelo_ia=modelo_ia,
        )

    def listar_por_documento(self, documento_id: UUID, usuario_id: UUID) -> list:
        return self.resumo_repo.listar_por_documento(documento_id, usuario_id)

    def obter_conteudo(self, resumo_id: UUID, usuario_id: UUID) -> dict:
        resumo = self.resumo_repo.buscar_por_id(resumo_id, usuario_id)
        if not resumo:
            raise ValueError("Resumo não encontrado ou não pertence ao usuário.")

        texto = self.s3_service.download_text(resumo["s3_chave"])
        return {"id": resumo["id"], "titulo": resumo["titulo"], "conteudo": texto}

    def deletar_resumo(self, resumo_id: UUID, usuario_id: UUID) -> bool:
        return self.resumo_repo.deletar(resumo_id, usuario_id)
