import logging
from uuid import UUID
from app.repositories.DashboardRepository import DashboardRepository
from app.schemas.dashboard_schema import DashboardResponse, FlashcardItem, ResumoItem, QuizItem

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo
        logger.info("DashboardService inicializado com sucesso.")

    def obter_dashboard_usuario(self, usuario_id: UUID) -> DashboardResponse:
        logger.info(f"Iniciando montagem do dashboard para o usuário {usuario_id}.")
        
        try:
            logger.debug(f"Buscando histórico recente de atividades (Usuário: {usuario_id})...")
            ultimos_flashcards = self.dashboard_repo.buscar_ultimos_flashcards(usuario_id)
            ultimos_resumos = self.dashboard_repo.buscar_ultimos_resumos(usuario_id)
            ultimos_quizzes = self.dashboard_repo.buscar_ultimos_quizzes(usuario_id)

            logger.debug(f"Buscando contadores totais (Usuário: {usuario_id})...")
            total_flashcards = self.dashboard_repo.contar_total_flashcards(usuario_id)
            total_resumos = self.dashboard_repo.contar_total_resumos(usuario_id)
            total_quizzes = self.dashboard_repo.contar_total_quizzes(usuario_id)

            logger.info(
                f"Dashboard montado com sucesso para {usuario_id}. "
                f"Métricas Totais -> Flashcards: {total_flashcards} | Resumos: {total_resumos} | Quizzes: {total_quizzes}"
            )

            return DashboardResponse(
                ultimos_flashcards=[FlashcardItem(**dict(row)) for row in ultimos_flashcards],
                ultimos_resumos=[ResumoItem(**dict(row)) for row in ultimos_resumos],
                ultimos_quizzes=[QuizItem(**dict(row)) for row in ultimos_quizzes],
                total_flashcards=total_flashcards,
                total_resumos=total_resumos,
                total_quizzes=total_quizzes,
            )
            
        except Exception as e:
            logger.error(f"Falha ao processar e montar o dashboard para o usuário {usuario_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível carregar os dados do dashboard no momento. Tente novamente mais tarde.")