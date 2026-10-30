from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status

from app.api.dependencies import (
    get_current_user_id,
    get_document_generator_service,
    get_flashcard_service,
    get_quiz_service,
    get_resumo_service,
)
from app.schemas.flashcard_schema import (
    FlashcardConteudoResponse,
    FlashcardCreateRequest,
    FlashcardRenomearRequest,
    FlashcardResponse,
)
from app.schemas.quiz_schema import (
    QuizConteudoResponse,
    QuizCreateRequest,
    QuizRenomearRequest,
    QuizResponse,
)
from app.schemas.resumo_schema import (
    ResumoConteudoResponse,
    ResumoCreateRequest,
    ResumoRenomearRequest,
    ResumoResponse,
)
from app.schemas.user_schema import (
    DocumentoBuscaResponse,
    Pasta,
    PastaConteudoResponse,
    PastaCreateRequest,
    PastaListagemResponse,
)
from app.services.DocumentGeneratorService import DocumentGeneratorService
from app.services.FlashcardService import FlashcardService
from app.services.QuizService import QuizService
from app.services.ResumoService import ResumoService

pastas_router = APIRouter(prefix="/pastas", tags=["pastas"])
documentos_router = APIRouter(prefix="/documentos", tags=["documentos"])
resumos_router = APIRouter(prefix="/resumos", tags=["resumos"])
flashcards_router = APIRouter(prefix="/flashcards", tags=["flashcards"])
quizzes_router = APIRouter(prefix="/quizzes", tags=["quizzes"])


# ============================================================================
# PASTAS
# ============================================================================
@pastas_router.post("", status_code=status.HTTP_201_CREATED)
async def criar_pasta(
    pasta: PastaCreateRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.criar_pasta_service(usuario_id, pasta.nome, pasta.pasta_pai_id)


@pastas_router.get("/user/{user_id}", response_model=list[PastaListagemResponse], status_code=status.HTTP_200_OK)
def listar_pastas_raiz(
    user_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> list:
    if usuario_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return service.listar_pastas_raiz_por_usuario(user_id, limit, offset)


@pastas_router.get("/user/{user_id}/todas", response_model=list[PastaListagemResponse], status_code=status.HTTP_200_OK)
def listar_todas_pastas_usuario(
    user_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> list:
    if usuario_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return service.listar_todas_pastas_por_usuario(user_id)


@pastas_router.get("/{pasta_id}/conteudo", response_model=PastaConteudoResponse, status_code=status.HTTP_200_OK)
def listar_conteudo_pasta(
    pasta_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.listar_conteudo_pasta(pasta_id, usuario_id, limit, offset)


@pastas_router.put("/{pasta_id}", response_model=Pasta, status_code=status.HTTP_200_OK)
def atualizar_pasta(
    pasta_id: UUID,
    nome: str = Form(...),
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> Pasta:
    return service.atualizar_pasta_nome(pasta_id, nome, usuario_id)


@pastas_router.delete("/{pasta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pasta(
    pasta_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> None:
    service.deletar_pasta(pasta_id, usuario_id)
    return None


# ============================================================================
# DOCUMENTOS
# ============================================================================
@documentos_router.post("/upload", status_code=status.HTTP_201_CREATED)
def salvar_documento(
    documento: UploadFile = File(...),
    pasta_id: UUID = Form(...),
    nome_documento: str = Form(...),
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.salvar_documento(documento, pasta_id, usuario_id, nome_documento)


@documentos_router.get("", response_model=DocumentoBuscaResponse, status_code=status.HTTP_200_OK)
def buscar_documentos(
    q: str = Query("", max_length=100),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service),
):
    return service.buscar_documentos(usuario_id, q, limit, offset)


def _resposta_pdf(conteudo: bytes, nome_arquivo: str) -> Response:
    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{nome_arquivo}"',
            "Cache-Control": "private, no-store",
        },
    )


@documentos_router.get("/{documento_id}/arquivo", status_code=status.HTTP_200_OK)
def obter_arquivo_documento(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service),
) -> Response:
    return _resposta_pdf(service.obter_arquivo_bytes(documento_id, usuario_id), "documento.pdf")


@documentos_router.get("/{documento_id}/url-visualizacao", status_code=status.HTTP_200_OK)
def obter_url_visualizacao(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> dict:
    url = service.gerar_pre_signed_url_visualizacao(documento_id, usuario_id)
    return {"url": url}


@documentos_router.put("/{documento_id}", status_code=status.HTTP_200_OK)
def atualizar_documento(
    documento_id: UUID,
    nome: str = Form(...),
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.atualizar_documento_nome(documento_id, nome, usuario_id)


@documentos_router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_documento(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> None:
    service.deletar_documento(documento_id, usuario_id)
    return None


# ============================================================================
# RESUMOS (via Bedrock)
# ============================================================================
@documentos_router.post(
    "/{documento_id}/resumos", response_model=ResumoResponse, status_code=status.HTTP_201_CREATED
)
def gerar_resumo(
    documento_id: UUID,
    payload: ResumoCreateRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ResumoService = Depends(get_resumo_service),
):
    return service.gerar_resumo(
        documento_id=documento_id,
        usuario_id=usuario_id,
        nivel_conhecimento=payload.nivel_conhecimento,
        formato=payload.formato.value,
        tom=payload.tom,
    )


@documentos_router.get(
    "/{documento_id}/resumos", response_model=list[ResumoResponse], status_code=status.HTTP_200_OK
)
def listar_resumos_do_documento(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ResumoService = Depends(get_resumo_service),
) -> list:
    return service.listar_por_documento(documento_id, usuario_id)


@resumos_router.get(
    "/{resumo_id}/conteudo", response_model=ResumoConteudoResponse, status_code=status.HTTP_200_OK
)
def obter_conteudo_resumo(
    resumo_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ResumoService = Depends(get_resumo_service),
):
    return service.obter_conteudo(resumo_id, usuario_id)


@resumos_router.get("/{resumo_id}/pdf", status_code=status.HTTP_200_OK)
def obter_pdf_resumo(
    resumo_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ResumoService = Depends(get_resumo_service),
) -> Response:
    return _resposta_pdf(service.obter_pdf_bytes(resumo_id, usuario_id), "resumo.pdf")


@resumos_router.get("/{resumo_id}/download", status_code=status.HTTP_200_OK)
def obter_download_pdf_resumo(
    resumo_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ResumoService = Depends(get_resumo_service),
) -> dict:
    url = service.obter_download_url(resumo_id, usuario_id)
    return {"url": url}


@resumos_router.put("/{resumo_id}", response_model=ResumoResponse, status_code=status.HTTP_200_OK)
def renomear_resumo(
    resumo_id: UUID,
    payload: ResumoRenomearRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ResumoService = Depends(get_resumo_service),
):
    return service.renomear_resumo(resumo_id, usuario_id, payload.titulo)


@resumos_router.delete("/{resumo_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_resumo(
    resumo_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ResumoService = Depends(get_resumo_service),
) -> None:
    service.deletar_resumo(resumo_id, usuario_id)
    return None


# ============================================================================
# FLASHCARDS (via Bedrock)
# ============================================================================
@documentos_router.post(
    "/{documento_id}/flashcards", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED
)
def gerar_flashcards(
    documento_id: UUID,
    payload: FlashcardCreateRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: FlashcardService = Depends(get_flashcard_service),
):
    return service.gerar_flashcards(documento_id, usuario_id, payload.quantidade, payload.dificuldade)


@documentos_router.get(
    "/{documento_id}/flashcards", response_model=list[FlashcardResponse], status_code=status.HTTP_200_OK
)
def listar_flashcards_do_documento(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: FlashcardService = Depends(get_flashcard_service),
) -> list:
    return service.listar_por_documento(documento_id, usuario_id)


@flashcards_router.get(
    "/{flashcard_id}/conteudo", response_model=FlashcardConteudoResponse, status_code=status.HTTP_200_OK
)
def obter_conteudo_flashcard(
    flashcard_id: UUID,
    somente_vencidos: bool = Query(False),
    usuario_id: UUID = Depends(get_current_user_id),
    service: FlashcardService = Depends(get_flashcard_service),
):
    return service.obter_conteudo(flashcard_id, usuario_id, somente_vencidos)


@flashcards_router.put("/{flashcard_id}", response_model=FlashcardResponse, status_code=status.HTTP_200_OK)
def renomear_flashcard(
    flashcard_id: UUID,
    payload: FlashcardRenomearRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: FlashcardService = Depends(get_flashcard_service),
):
    return service.renomear_flashcard(flashcard_id, usuario_id, payload.titulo)


@flashcards_router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_flashcard(
    flashcard_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: FlashcardService = Depends(get_flashcard_service),
) -> None:
    service.deletar_flashcard(flashcard_id, usuario_id)
    return None


# ============================================================================
# QUIZZES (via Bedrock)
# ============================================================================
@documentos_router.post(
    "/{documento_id}/quizzes", response_model=QuizResponse, status_code=status.HTTP_201_CREATED
)
def gerar_quiz(
    documento_id: UUID,
    payload: QuizCreateRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: QuizService = Depends(get_quiz_service),
):
    return service.gerar_quiz(documento_id, usuario_id, payload.quantidade, payload.dificuldade)


@documentos_router.get(
    "/{documento_id}/quizzes", response_model=list[QuizResponse], status_code=status.HTTP_200_OK
)
def listar_quizzes_do_documento(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: QuizService = Depends(get_quiz_service),
) -> list:
    return service.listar_por_documento(documento_id, usuario_id)


@quizzes_router.get(
    "/{quiz_id}/conteudo", response_model=QuizConteudoResponse, status_code=status.HTTP_200_OK
)
def obter_conteudo_quiz(
    quiz_id: UUID,
    somente_vencidos: bool = Query(False),
    usuario_id: UUID = Depends(get_current_user_id),
    service: QuizService = Depends(get_quiz_service),
):
    return service.obter_conteudo(quiz_id, usuario_id, somente_vencidos)


@quizzes_router.put("/{quiz_id}", response_model=QuizResponse, status_code=status.HTTP_200_OK)
def renomear_quiz(
    quiz_id: UUID,
    payload: QuizRenomearRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: QuizService = Depends(get_quiz_service),
):
    return service.renomear_quiz(quiz_id, usuario_id, payload.titulo)


@quizzes_router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_quiz(
    quiz_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: QuizService = Depends(get_quiz_service),
) -> None:
    service.deletar_quiz(quiz_id, usuario_id)
    return None
