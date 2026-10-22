# app/api/dependencies.py
from fastapi import Depends, Header, HTTPException, Request, status
from uuid import UUID
from app.core import auth_middleware
from app.core.database import get_db_connection
from app.repositories.DashboardRepository import DashboardRepository
from app.repositories.DocumentRepository import DocumentRepository
from app.repositories.FlashcardRepository import FlashcardRepository
from app.repositories.ProfileRepository import ProfileRepository
from app.repositories.QuizRepository import QuizRepository
from app.repositories.ResumoRepository import ResumoRepository
from app.repositories.RevisaoRepository import RevisaoRepository
from app.services.DashboardService import DashboardService
from app.services.DocumentGeneratorService import DocumentGeneratorService
from app.services.FlashcardService import FlashcardService
from app.services.ProfileService import ProfileService
from app.services.QuizService import QuizService
from app.services.ResumoService import ResumoService
from app.services.RevisaoService import RevisaoService

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# Profile 
def get_profile_repository(conn = Depends(get_db)) -> ProfileRepository:
    return ProfileRepository(conn)

def get_profile_service(repo: ProfileRepository = Depends(get_profile_repository)) -> ProfileService:
    return ProfileService(repo)

# Document
def get_document_repository(conn = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(conn)

def get_document_generator_service(repo: DocumentRepository = Depends(get_document_repository)) -> DocumentGeneratorService:
    return DocumentGeneratorService(repo)

def get_current_user_id(
    request: Request,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    repo: ProfileRepository = Depends(get_profile_repository),
) -> UUID:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabeçalho X-User-Id é obrigatório"
        )

    try:
        user_id = UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id inválido"
        )

    if not auth_middleware.REQUIRE_AUTH:
        return user_id

    claims = getattr(request.state, "token_claims", None)
    cognito_id = claims.get("sub") if claims else None
    if not cognito_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido ou malformado."
        )

    if repo.buscar_id_por_cognito_id(cognito_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    return user_id

# Dashboard
def get_dashboard_repository(conn = Depends(get_db)) -> DashboardRepository:
    return DashboardRepository(conn)

def get_dashboard_service(repo: DashboardRepository = Depends(get_dashboard_repository)) -> DashboardService:
    return DashboardService(repo)

# Resumo
def get_resumo_repository(conn = Depends(get_db)) -> ResumoRepository:
    return ResumoRepository(conn)

def get_resumo_service(
    resumo_repo: ResumoRepository = Depends(get_resumo_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> ResumoService:
    return ResumoService(resumo_repo, document_repo)

# Flashcard
def get_flashcard_repository(conn = Depends(get_db)) -> FlashcardRepository:
    return FlashcardRepository(conn)

def get_flashcard_service(
    flashcard_repo: FlashcardRepository = Depends(get_flashcard_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> FlashcardService:
    return FlashcardService(flashcard_repo, document_repo)

# Quiz
def get_quiz_repository(conn = Depends(get_db)) -> QuizRepository:
    return QuizRepository(conn)

def get_quiz_service(
    quiz_repo: QuizRepository = Depends(get_quiz_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> QuizService:
    return QuizService(quiz_repo, document_repo)

# Revisão (Spaced Repetition / Daily Mix)
def get_revisao_repository(conn = Depends(get_db)) -> RevisaoRepository:
    return RevisaoRepository(conn)

def get_revisao_service(repo: RevisaoRepository = Depends(get_revisao_repository)) -> RevisaoService:
    return RevisaoService(repo)
