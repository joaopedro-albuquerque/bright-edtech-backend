from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.api import dependencies


@pytest.fixture(autouse=True)
def _mock_infra_services(mocker):
    """Isola os testes de DI da construção real de S3Service/BedrockService,
    que dependem de variáveis de ambiente (S3_BUCKET_NAME) inexistentes em CI."""
    mocker.patch("app.services.DocumentGeneratorService.S3Service")
    mocker.patch("app.services.DocumentGeneratorService.BedrockService")
    mocker.patch("app.services.ResumoService.S3Service")
    mocker.patch("app.services.ResumoService.BedrockService")
    mocker.patch("app.services.FlashcardService.S3Service")
    mocker.patch("app.services.FlashcardService.BedrockService")
    mocker.patch("app.services.QuizService.S3Service")
    mocker.patch("app.services.QuizService.BedrockService")
    mocker.patch("app.services.RevisaoService.S3Service")


class TestGetDb:
    def test_get_db_entrega_conexao_e_fecha_no_final(self, mocker):
        mock_conn = mocker.MagicMock()
        mocker.patch("app.api.dependencies.get_db_connection", return_value=mock_conn)

        gerador = dependencies.get_db()
        conn_entregue = next(gerador)

        assert conn_entregue is mock_conn
        mock_conn.close.assert_not_called()

        with pytest.raises(StopIteration):
            next(gerador)

        mock_conn.close.assert_called_once()

    def test_get_db_fecha_conexao_mesmo_quando_consumidor_falha(self, mocker):
        mock_conn = mocker.MagicMock()
        mocker.patch("app.api.dependencies.get_db_connection", return_value=mock_conn)

        gerador = dependencies.get_db()
        next(gerador)

        with pytest.raises(ValueError):
            gerador.throw(ValueError("falha no consumidor"))

        mock_conn.close.assert_called_once()


class TestGetCurrentUserId:
    def test_com_uuid_valido_retorna_uuid(self):
        user_id = uuid4()

        resultado = dependencies.get_current_user_id(x_user_id=str(user_id))

        assert resultado == user_id

    def test_sem_header_levanta_401(self):
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_current_user_id(x_user_id=None)

        assert exc_info.value.status_code == 401

    def test_com_uuid_invalido_levanta_400(self):
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_current_user_id(x_user_id="nao-e-um-uuid")

        assert exc_info.value.status_code == 400


class TestFabricasDeRepositorioEServico:
    def test_get_profile_repository_usa_conexao_fornecida(self, mocker):
        conn = mocker.MagicMock()

        repo = dependencies.get_profile_repository(conn)

        assert repo.conn is conn

    def test_get_profile_service_usa_repositorio_fornecido(self, mocker):
        repo = mocker.MagicMock()

        service = dependencies.get_profile_service(repo)

        assert service.repo is repo

    def test_get_document_repository_usa_conexao_fornecida(self, mocker):
        conn = mocker.MagicMock()

        repo = dependencies.get_document_repository(conn)

        assert repo.conn is conn

    def test_get_document_generator_service_usa_repositorio_fornecido(self, mocker):
        repo = mocker.MagicMock()

        service = dependencies.get_document_generator_service(repo)

        assert service.document_repo is repo

    def test_get_dashboard_repository_usa_conexao_fornecida(self, mocker):
        conn = mocker.MagicMock()

        repo = dependencies.get_dashboard_repository(conn)

        assert repo.conn is conn

    def test_get_dashboard_service_usa_repositorio_fornecido(self, mocker):
        repo = mocker.MagicMock()

        service = dependencies.get_dashboard_service(repo)

        assert service.dashboard_repo is repo

    def test_get_resumo_repository_usa_conexao_fornecida(self, mocker):
        conn = mocker.MagicMock()

        repo = dependencies.get_resumo_repository(conn)

        assert repo.conn is conn

    def test_get_resumo_service_usa_repositorios_fornecidos(self, mocker):
        resumo_repo = mocker.MagicMock()
        document_repo = mocker.MagicMock()

        service = dependencies.get_resumo_service(resumo_repo, document_repo)

        assert service.resumo_repo is resumo_repo
        assert service.document_repo is document_repo

    def test_get_flashcard_repository_usa_conexao_fornecida(self, mocker):
        conn = mocker.MagicMock()

        repo = dependencies.get_flashcard_repository(conn)

        assert repo.conn is conn

    def test_get_flashcard_service_usa_repositorios_fornecidos(self, mocker):
        flashcard_repo = mocker.MagicMock()
        document_repo = mocker.MagicMock()

        service = dependencies.get_flashcard_service(flashcard_repo, document_repo)

        assert service.flashcard_repo is flashcard_repo
        assert service.document_repo is document_repo

    def test_get_quiz_repository_usa_conexao_fornecida(self, mocker):
        conn = mocker.MagicMock()

        repo = dependencies.get_quiz_repository(conn)

        assert repo.conn is conn

    def test_get_quiz_service_usa_repositorios_fornecidos(self, mocker):
        quiz_repo = mocker.MagicMock()
        document_repo = mocker.MagicMock()

        service = dependencies.get_quiz_service(quiz_repo, document_repo)

        assert service.quiz_repo is quiz_repo
        assert service.document_repo is document_repo

    def test_get_revisao_repository_usa_conexao_fornecida(self, mocker):
        conn = mocker.MagicMock()

        repo = dependencies.get_revisao_repository(conn)

        assert repo.conn is conn

    def test_get_revisao_service_usa_repositorio_fornecido(self, mocker):
        repo = mocker.MagicMock()

        service = dependencies.get_revisao_service(repo)

        assert service.revisao_repo is repo
