from uuid import uuid4

import pytest

from app.core.exceptions import DashboardDatabaseError
from app.repositories.DashboardRepository import DashboardRepository


@pytest.fixture
def repo(mock_conn):
    return DashboardRepository(mock_conn)


@pytest.mark.parametrize(
    "metodo",
    [
        "buscar_ultimos_flashcards",
        "buscar_ultimos_resumos",
        "buscar_ultimos_quizzes",
        "buscar_documentos_recentes",
    ],
)
class TestMetodosDeListagem:
    def test_retorna_lista_quando_banco_responde(self, repo, mock_cursor, metodo):
        mock_cursor.fetchall.return_value = [{"id": uuid4(), "nome": "Item"}]

        resultado = getattr(repo, metodo)(uuid4())

        assert resultado == [{"id": resultado[0]["id"], "nome": "Item"}]

    def test_levanta_dashboard_database_error_quando_banco_falha(self, repo, mock_cursor, metodo):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DashboardDatabaseError):
            getattr(repo, metodo)(uuid4())


@pytest.mark.parametrize(
    "metodo",
    ["contar_total_flashcards", "contar_total_resumos", "contar_total_quizzes"],
)
class TestMetodosDeContagem:
    def test_retorna_total_quando_banco_responde(self, repo, mock_cursor, metodo):
        mock_cursor.fetchone.return_value = {"total": 42}

        resultado = getattr(repo, metodo)(uuid4())

        assert resultado == 42

    def test_retorna_zero_quando_banco_nao_retorna_linha(self, repo, mock_cursor, metodo):
        mock_cursor.fetchone.return_value = None

        resultado = getattr(repo, metodo)(uuid4())

        assert resultado == 0

    def test_levanta_dashboard_database_error_quando_banco_falha(self, repo, mock_cursor, metodo):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DashboardDatabaseError):
            getattr(repo, metodo)(uuid4())
