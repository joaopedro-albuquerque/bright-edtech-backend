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
    @pytest.fixture
    def request_com_token(self, mocker):
        request = mocker.MagicMock()
        request.state.token_claims = {"sub": "cognito-abc"}
        return request

    @pytest.fixture(autouse=True)
    def _auth_ligada(self, mocker):
        mocker.patch("app.api.dependencies.auth_middleware.REQUIRE_AUTH", True)

    def test_com_uuid_do_dono_do_token_retorna_uuid(self, mocker, request_com_token):
        user_id = uuid4()
        repo = mocker.MagicMock()
        repo.buscar_id_por_cognito_id.return_value = user_id

        resultado = dependencies.get_current_user_id(request_com_token, str(user_id), repo)

        assert resultado == user_id
        repo.buscar_id_por_cognito_id.assert_called_once_with("cognito-abc")

    def test_com_uuid_de_outro_usuario_levanta_403(self, mocker, request_com_token):
        repo = mocker.MagicMock()
        repo.buscar_id_por_cognito_id.return_value = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_current_user_id(request_com_token, str(uuid4()), repo)

        assert exc_info.value.status_code == 403

    def test_com_usuario_inexistente_para_o_token_levanta_403(self, mocker, request_com_token):
        repo = mocker.MagicMock()
        repo.buscar_id_por_cognito_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_current_user_id(request_com_token, str(uuid4()), repo)

        assert exc_info.value.status_code == 403

    def test_sem_claims_no_request_levanta_401(self, mocker):
        request = mocker.MagicMock()
        request.state.token_claims = None

        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_current_user_id(request, str(uuid4()), mocker.MagicMock())

        assert exc_info.value.status_code == 401

    def test_sem_header_levanta_401(self, mocker, request_com_token):
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_current_user_id(request_com_token, None, mocker.MagicMock())

        assert exc_info.value.status_code == 401

    def test_com_uuid_invalido_levanta_400(self, mocker, request_com_token):
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_current_user_id(request_com_token, "nao-e-um-uuid", mocker.MagicMock())

        assert exc_info.value.status_code == 400

    def test_com_auth_desligada_nao_confere_o_token(self, mocker):
        mocker.patch("app.api.dependencies.auth_middleware.REQUIRE_AUTH", False)
        user_id = uuid4()
        repo = mocker.MagicMock()

        resultado = dependencies.get_current_user_id(mocker.MagicMock(), str(user_id), repo)

        assert resultado == user_id
        repo.buscar_id_por_cognito_id.assert_not_called()


class TestGetCurrentUserIdNaRota:
    @pytest.fixture
    def client_factory(self, mocker):
        from fastapi import Depends, FastAPI, Request
        from fastapi.testclient import TestClient

        mocker.patch("app.api.dependencies.auth_middleware.REQUIRE_AUTH", True)

        def build(id_do_dono):
            app = FastAPI()

            @app.middleware("http")
            async def injeta_claims(request: Request, call_next):
                request.state.token_claims = {"sub": "cognito-abc"}
                return await call_next(request)

            @app.get("/dados")
            def dados(usuario_id: UUID = Depends(dependencies.get_current_user_id)):
                return {"id": str(usuario_id)}

            repo = mocker.MagicMock()
            repo.buscar_id_por_cognito_id.return_value = id_do_dono
            app.dependency_overrides[dependencies.get_profile_repository] = lambda: repo
            return TestClient(app)

        return build

    def test_x_user_id_do_dono_do_token_retorna_200(self, client_factory):
        dono = uuid4()

        resposta = client_factory(dono).get("/dados", headers={"X-User-Id": str(dono)})

        assert resposta.status_code == 200
        assert resposta.json() == {"id": str(dono)}

    def test_x_user_id_de_outro_usuario_retorna_403(self, client_factory):
        resposta = client_factory(uuid4()).get("/dados", headers={"X-User-Id": str(uuid4())})

        assert resposta.status_code == 403


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
