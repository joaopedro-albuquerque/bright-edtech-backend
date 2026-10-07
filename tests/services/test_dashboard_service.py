from uuid import uuid4

import pytest

from app.core.exceptions import DashboardDatabaseError
from app.services.DashboardService import DashboardService


@pytest.fixture
def dashboard_repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def service(dashboard_repo):
    return DashboardService(dashboard_repo)


def test_obter_dashboard_usuario_com_sucesso_monta_resposta_agregada(service, dashboard_repo):
    dashboard_repo.buscar_ultimos_flashcards.return_value = [{"id": uuid4(), "titulo": "F", "criado_em": "2026-01-01"}]
    dashboard_repo.buscar_ultimos_resumos.return_value = [{"id": uuid4(), "nome": "R", "criado_em": "2026-01-01"}]
    dashboard_repo.buscar_ultimos_quizzes.return_value = [{"id": uuid4(), "titulo": "Q", "criado_em": "2026-01-01"}]
    dashboard_repo.buscar_documentos_recentes.return_value = [{"id": uuid4(), "nome": "D", "criado_em": "2026-01-01"}]
    dashboard_repo.contar_total_flashcards.return_value = 3
    dashboard_repo.contar_total_resumos.return_value = 2
    dashboard_repo.contar_total_quizzes.return_value = 1

    resultado = service.obter_dashboard_usuario(uuid4())

    assert resultado.total_flashcards == 3
    assert resultado.total_resumos == 2
    assert resultado.total_quizzes == 1
    assert len(resultado.ultimos_flashcards) == 1
    assert len(resultado.documentos_recentes) == 1


def test_obter_dashboard_usuario_propaga_erro_quando_repositorio_falha(service, dashboard_repo):
    dashboard_repo.buscar_ultimos_flashcards.side_effect = DashboardDatabaseError("falha no banco")

    with pytest.raises(DashboardDatabaseError):
        service.obter_dashboard_usuario(uuid4())
