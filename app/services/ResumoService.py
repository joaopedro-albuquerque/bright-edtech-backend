import logging
from uuid import UUID

from app.core.exceptions import DocumentNotFoundError, ResumoNotFoundError
from app.repositories.DocumentRepository import DocumentRepository
from app.repositories.ResumoRepository import ResumoRepository
from app.services.BedrockService import BedrockService
from app.services.S3Service import S3Service
from app.services.pdf_generator import gerar_pdf_de_markdown
from app.services.pdf_utils import ler_bytes

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
            raise DocumentNotFoundError("Documento não encontrado ou não pertence ao usuário.")

        pdf_bytes = ler_bytes(self.s3_service.download_file(documento["chave_s3"]))

        texto_gerado, tokens_utilizados, modelo_ia = self.bedrock_service.gerar_resumo(
            pdf_bytes, formato, nivel_conhecimento, tom
        )

        titulo = f"Resumo ({formato})"
        s3_chave = self.s3_service.build_artifact_key(usuario_id, documento_id, f"resumo-{formato}.md")
        self.s3_service.upload_text(texto_gerado, s3_chave)

        s3_chave_pdf = self.s3_service.build_artifact_key(usuario_id, documento_id, f"resumo-{formato}.pdf")
        try:
            pdf_bytes = gerar_pdf_de_markdown(texto_gerado, titulo)
            self.s3_service.upload_bytes(pdf_bytes, s3_chave_pdf, content_type="application/pdf")
        except Exception:
            logger.warning(f"Falha ao gerar PDF do resumo (documento {documento_id}).", exc_info=True)
            s3_chave_pdf = None

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
            s3_chave_pdf=s3_chave_pdf,
        )

    def listar_por_documento(self, documento_id: UUID, usuario_id: UUID) -> list:
        return self.resumo_repo.listar_por_documento(documento_id, usuario_id)

    def obter_conteudo(self, resumo_id: UUID, usuario_id: UUID) -> dict:
        resumo = self.resumo_repo.buscar_por_id(resumo_id, usuario_id)
        if not resumo:
            raise ResumoNotFoundError("Resumo não encontrado ou não pertence ao usuário.")

        texto = self.s3_service.download_text(resumo["s3_chave"])
        return {"id": resumo["id"], "titulo": resumo["titulo"], "conteudo": texto}

    def _buscar_resumo(self, resumo_id: UUID, usuario_id: UUID) -> dict:
        resumo = self.resumo_repo.buscar_por_id(resumo_id, usuario_id)
        if not resumo:
            raise ResumoNotFoundError("Resumo não encontrado ou não pertence ao usuário.")
        return resumo

    def _garantir_pdf(self, resumo: dict, resumo_id: UUID, usuario_id: UUID) -> str:
        """Chave S3 do PDF do resumo; gera o PDF a partir do markdown se ainda não existir."""
        s3_chave_pdf = resumo.get("s3_chave_pdf")
        if not s3_chave_pdf:
            texto_markdown = self.s3_service.download_text(resumo["s3_chave"])
            pdf_bytes = gerar_pdf_de_markdown(texto_markdown, resumo["titulo"])
            s3_chave_pdf = self.s3_service.build_artifact_key(
                usuario_id, resumo["documento_id"], f"resumo-{resumo['formato']}.pdf"
            )
            self.s3_service.upload_bytes(pdf_bytes, s3_chave_pdf, content_type="application/pdf")
            self.resumo_repo.atualizar_s3_chave_pdf(resumo_id, usuario_id, s3_chave_pdf)
        return s3_chave_pdf

    def obter_download_url(self, resumo_id: UUID, usuario_id: UUID) -> str:
        resumo = self._buscar_resumo(resumo_id, usuario_id)
        return self.s3_service.generate_presigned_url(self._garantir_pdf(resumo, resumo_id, usuario_id))

    def obter_pdf_bytes(self, resumo_id: UUID, usuario_id: UUID) -> bytes:
        resumo = self._buscar_resumo(resumo_id, usuario_id)
        return self.s3_service.download_file(self._garantir_pdf(resumo, resumo_id, usuario_id)).read()

    def renomear_resumo(self, resumo_id: UUID, usuario_id: UUID, titulo: str) -> dict:
        resultado = self.resumo_repo.atualizar_titulo(resumo_id, usuario_id, titulo)
        if not resultado:
            raise ResumoNotFoundError("Resumo não encontrado.")
        return resultado

    def deletar_resumo(self, resumo_id: UUID, usuario_id: UUID) -> None:
        deleted = self.resumo_repo.deletar(resumo_id, usuario_id)
        if not deleted:
            raise ResumoNotFoundError("Resumo não encontrado.")
