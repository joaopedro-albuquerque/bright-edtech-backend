import logging
from uuid import UUID

from app.core.exceptions import DocumentNotFoundError, QuizNotFoundError
from app.repositories.DocumentRepository import DocumentRepository
from app.repositories.QuizRepository import QuizRepository
from app.services.BedrockService import BedrockService
from app.services.S3Service import S3Service
from app.services.pdf_utils import extrair_texto_do_pdf

logger = logging.getLogger(__name__)


class QuizService:
    def __init__(
        self,
        quiz_repo: QuizRepository,
        document_repo: DocumentRepository,
        s3_service: S3Service | None = None,
        bedrock_service: BedrockService | None = None,
    ):
        self.quiz_repo = quiz_repo
        self.document_repo = document_repo
        self.s3_service = s3_service or S3Service()
        self.bedrock_service = bedrock_service or BedrockService()

    def gerar_quiz(self, documento_id: UUID, usuario_id: UUID, quantidade: int = 10, dificuldade: str = "medio") -> dict:
        logger.info(f"Gerando quiz com {quantidade} questões (dificuldade={dificuldade}) para documento {documento_id}.")

        documento = self.document_repo.buscar_chave_s3_por_documento_id_e_usuario(documento_id, usuario_id)
        if not documento or not documento.get("chave_s3"):
            raise DocumentNotFoundError("Documento não encontrado ou não pertence ao usuário.")

        arquivo_pdf = self.s3_service.download_file(documento["chave_s3"])
        texto_extraido = extrair_texto_do_pdf(arquivo_pdf)

        questoes_json, tokens_utilizados, modelo_ia = self.bedrock_service.gerar_quiz(
            texto_extraido, quantidade, dificuldade
        )

        titulo = "Quiz Gerado"
        s3_chave = f"artifacts/{usuario_id}/{documento_id}/quiz-{quantidade}.json"
        self.s3_service.upload_json(questoes_json, s3_chave)

        item_refs = [questao["item_ref"] for questao in questoes_json]

        return self.quiz_repo.criar_quiz_com_questoes(
            usuario_id=usuario_id,
            documento_id=documento_id,
            titulo=titulo,
            s3_chave=s3_chave,
            tokens_utilizados=tokens_utilizados,
            modelo_ia=modelo_ia,
            item_refs=item_refs,
        )

    def listar_por_documento(self, documento_id: UUID, usuario_id: UUID) -> list:
        return self.quiz_repo.listar_por_documento(documento_id, usuario_id)

    def obter_conteudo(self, quiz_id: UUID, usuario_id: UUID) -> dict:
        quiz = self.quiz_repo.buscar_por_id(quiz_id, usuario_id)
        if not quiz:
            raise QuizNotFoundError("Quiz não encontrado ou não pertence ao usuário.")

        questoes = self.quiz_repo.listar_questoes_por_quiz(quiz_id, usuario_id)

        try:
            itens_json = self.s3_service.download_json(quiz["s3_chave"])
        except Exception:
            logger.warning(f"Falha ao baixar conteúdo do S3: {quiz['s3_chave']}", exc_info=True)
            itens_json = []

        questoes_enriquecidas = []
        for questao in questoes:
            conteudo_item = next(
                (i for i in itens_json if i.get("item_ref") == questao["item_ref"]), None
            )
            questoes_enriquecidas.append({**questao, "conteudo": conteudo_item})

        return {"id": quiz["id"], "titulo": quiz["titulo"], "questoes": questoes_enriquecidas}

    def renomear_quiz(self, quiz_id: UUID, usuario_id: UUID, titulo: str) -> dict:
        resultado = self.quiz_repo.atualizar_titulo(quiz_id, usuario_id, titulo)
        if not resultado:
            raise QuizNotFoundError("Quiz não encontrado.")
        return resultado

    def deletar_quiz(self, quiz_id: UUID, usuario_id: UUID) -> None:
        deleted = self.quiz_repo.deletar(quiz_id, usuario_id)
        if not deleted:
            raise QuizNotFoundError("Quiz não encontrado.")
