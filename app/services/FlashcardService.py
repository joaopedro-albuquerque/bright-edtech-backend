import logging
from uuid import UUID

from app.repositories.DocumentRepository import DocumentRepository
from app.repositories.FlashcardRepository import FlashcardRepository
from app.services.BedrockService import BedrockService
from app.services.S3Service import S3Service
from app.services.pdf_utils import extrair_texto_do_pdf

logger = logging.getLogger(__name__)


class FlashcardService:
    def __init__(
        self,
        flashcard_repo: FlashcardRepository,
        document_repo: DocumentRepository,
        s3_service: S3Service | None = None,
        bedrock_service: BedrockService | None = None,
    ):
        self.flashcard_repo = flashcard_repo
        self.document_repo = document_repo
        self.s3_service = s3_service or S3Service()
        self.bedrock_service = bedrock_service or BedrockService()

    def gerar_flashcards(self, documento_id: UUID, usuario_id: UUID, quantidade: int = 10) -> dict:
        logger.info(f"Gerando {quantidade} flashcards para documento {documento_id}.")

        documento = self.document_repo.buscar_chave_s3_por_documento_id_e_usuario(documento_id, usuario_id)
        if not documento or not documento.get("chave_s3"):
            raise ValueError("Documento não encontrado ou não pertence ao usuário.")

        arquivo_pdf = self.s3_service.download_file(documento["chave_s3"])
        texto_extraido = extrair_texto_do_pdf(arquivo_pdf)

        cartoes_json, tokens_utilizados, modelo_ia = self.bedrock_service.gerar_flashcards(
            texto_extraido, quantidade
        )

        titulo = "Flashcards Gerados"
        s3_chave = f"artifacts/{usuario_id}/{documento_id}/flashcard-{quantidade}.json"
        self.s3_service.upload_json(cartoes_json, s3_chave)

        item_refs = [card["item_ref"] for card in cartoes_json]

        return self.flashcard_repo.criar_flashcard_com_cartoes(
            usuario_id=usuario_id,
            documento_id=documento_id,
            titulo=titulo,
            s3_chave=s3_chave,
            tokens_utilizados=tokens_utilizados,
            modelo_ia=modelo_ia,
            item_refs=item_refs,
        )

    def listar_por_documento(self, documento_id: UUID, usuario_id: UUID) -> list:
        return self.flashcard_repo.listar_por_documento(documento_id, usuario_id)

    def obter_conteudo(self, flashcard_id: UUID, usuario_id: UUID) -> dict:
        flashcard = self.flashcard_repo.buscar_por_id(flashcard_id, usuario_id)
        if not flashcard:
            raise ValueError("Flashcard não encontrado ou não pertence ao usuário.")

        cartoes = self.flashcard_repo.listar_cartoes_por_flashcard(flashcard_id, usuario_id)

        try:
            itens_json = self.s3_service.download_json(flashcard["s3_chave"])
        except Exception:
            logger.warning(f"Falha ao baixar conteúdo do S3: {flashcard['s3_chave']}", exc_info=True)
            itens_json = []

        cartoes_enriquecidos = []
        for cartao in cartoes:
            conteudo_item = next(
                (i for i in itens_json if i.get("item_ref") == cartao["item_ref"]), None
            )
            cartoes_enriquecidos.append({**cartao, "conteudo": conteudo_item})

        return {"id": flashcard["id"], "titulo": flashcard["titulo"], "cartoes": cartoes_enriquecidos}

    def deletar_flashcard(self, flashcard_id: UUID, usuario_id: UUID) -> bool:
        return self.flashcard_repo.deletar(flashcard_id, usuario_id)
