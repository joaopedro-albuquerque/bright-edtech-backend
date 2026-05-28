from uuid import UUID
from app.repositories.DashboardRepository import DashboardRepository
from app.schemas.dashboard_schema import DashboardResponse, FlashcardItem, ResumoItem, QuizItem

class DashboardService:
    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def obter_dashboard_usuario(self, usuario_id: UUID) -> DashboardResponse:
        ultimos_flashcards = self.dashboard_repo.buscar_ultimos_flashcards(usuario_id)
        ultimos_resumos = self.dashboard_repo.buscar_ultimos_resumos(usuario_id)
        ultimos_quizzes = self.dashboard_repo.buscar_ultimos_quizzes(usuario_id)

        total_flashcards = self.dashboard_repo.contar_total_flashcards(usuario_id)
        total_resumos = self.dashboard_repo.contar_total_resumos(usuario_id)
        total_quizzes = self.dashboard_repo.contar_total_quizzes(usuario_id)

        return DashboardResponse(
            ultimos_flashcards=[FlashcardItem(**dict(row)) for row in ultimos_flashcards],
            ultimos_resumos=[ResumoItem(**dict(row)) for row in ultimos_resumos],
            ultimos_quizzes=[QuizItem(**dict(row)) for row in ultimos_quizzes],
            total_flashcards=total_flashcards,
            total_resumos=total_resumos,
            total_quizzes=total_quizzes,
        )
