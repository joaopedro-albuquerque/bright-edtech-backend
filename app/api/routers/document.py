from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.api.dependencies import (
    get_current_user_id,
    get_document_generator_service,
    get_flashcard_service,
    get_quiz_service,
    get_resumo_service,
)
from app.schemas.flashcard_schema import FlashcardCreateRequest, FlashcardResponse
from app.schemas.quiz_schema import QuizCreateRequest, QuizResponse
from app.schemas.resumo_schema import ResumoCreateRequest, ResumoResponse
from app.schemas.user_schema import Pasta, PastaBase, PastaConteudoResponse, PastaListagemResponse
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
    pasta: PastaBase,
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.criar_pasta_service(pasta)


@pastas_router.get("/user/{user_id}", response_model=list[PastaListagemResponse], status_code=status.HTTP_200_OK)
def listar_pastas_raiz(
    user_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> list:
    return service.listar_pastas_raiz_por_usuario(user_id, limit, offset)


@pastas_router.get("/user/{user_id}/todas", response_model=list[PastaListagemResponse], status_code=status.HTTP_200_OK)
def listar_todas_pastas_usuario(
    user_id: UUID,
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> list:
    return service.listar_todas_pastas_por_usuario(user_id)


@pastas_router.get("/{pasta_id}/conteudo", response_model=PastaConteudoResponse, status_code=status.HTTP_200_OK)
def listar_conteudo_pasta(
    pasta_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.listar_conteudo_pasta(pasta_id, limit, offset)


@pastas_router.put("/{pasta_id}", response_model=Pasta, status_code=status.HTTP_200_OK)
def atualizar_pasta(
    pasta_id: UUID,
    nome: str = Form(...),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> Pasta:
    pasta_atualizada = service.atualizar_pasta_nome(pasta_id, nome)
    if not pasta_atualizada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pasta não encontrada")
    return pasta_atualizada


@pastas_router.delete("/{pasta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pasta(
    pasta_id: UUID,
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> None:
    deleted = service.deletar_pasta(pasta_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pasta não encontrada")
    return None


# ============================================================================
# DOCUMENTOS
# ============================================================================
@documentos_router.post("/upload", status_code=status.HTTP_201_CREATED)
def salvar_documento(
    documento: UploadFile = File(...),
    pasta_id: UUID = Form(...),
    user_id: UUID = Form(...),
    nome_documento: str = Form(...),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.salvar_documento(documento, pasta_id, user_id, nome_documento)


@documentos_router.get("/{documento_id}/url-visualizacao", status_code=status.HTTP_200_OK)
def obter_url_visualizacao(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> dict:
    try:
        url = service.gerar_pre_signed_url_visualizacao(documento_id, usuario_id)
        return {"url": url}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@documentos_router.put("/{documento_id}", status_code=status.HTTP_200_OK)
def atualizar_documento(
    documento_id: UUID,
    nome: str = Form(...),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    documento_atualizado = service.atualizar_documento_nome(documento_id, nome)
    if not documento_atualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")
    return documento_atualizado


@documentos_router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_documento(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> None:
    deleted = service.deletar_documento(documento_id, usuario_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")
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
    try:
        return service.gerar_resumo(
            documento_id=documento_id,
            usuario_id=usuario_id,
            nivel_conhecimento=payload.nivel_conhecimento,
            formato=payload.formato.value,
            tom=payload.tom,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@resumos_router.delete("/{resumo_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_resumo(
    resumo_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ResumoService = Depends(get_resumo_service),
) -> None:
    deleted = service.deletar_resumo(resumo_id, usuario_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resumo não encontrado")
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
    try:
        return service.gerar_flashcards(documento_id, usuario_id, payload.quantidade)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@flashcards_router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_flashcard(
    flashcard_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: FlashcardService = Depends(get_flashcard_service),
) -> None:
    deleted = service.deletar_flashcard(flashcard_id, usuario_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard não encontrado")
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
    try:
        return service.gerar_quiz(documento_id, usuario_id, payload.quantidade)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@quizzes_router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_quiz(
    quiz_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: QuizService = Depends(get_quiz_service),
) -> None:
    deleted = service.deletar_quiz(quiz_id, usuario_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz não encontrado")
    return None
