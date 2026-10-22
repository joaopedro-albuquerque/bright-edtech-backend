from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.dependencies import get_current_user_id, get_dashboard_service, get_profile_service
from app.api.routers.profile import router
from app.core.config import TERMOS_DE_USO_VERSAO
from app.core.exceptions import ProfileNotFoundError, ValidationNotificationError
from app.schemas.dashboard_schema import DashboardResponse


class _FakeAuthClaimsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.token_claims = {"sub": "cognito-id-123"}
        return await call_next(request)


@pytest.fixture
def usuario_id():
    return uuid4()


@pytest.fixture
def profile_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def dashboard_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def client(app_factory, usuario_id, profile_service, dashboard_service):
    app = app_factory(router)
    app.dependency_overrides[get_current_user_id] = lambda: usuario_id
    app.dependency_overrides[get_profile_service] = lambda: profile_service
    app.dependency_overrides[get_dashboard_service] = lambda: dashboard_service
    return TestClient(app)


@pytest.fixture
def client_com_token_valido(app_factory, profile_service, dashboard_service):
    app = app_factory(router)
    app.add_middleware(_FakeAuthClaimsMiddleware)
    app.dependency_overrides[get_profile_service] = lambda: profile_service
    app.dependency_overrides[get_dashboard_service] = lambda: dashboard_service
    return TestClient(app)


def _usuario_dict(**overrides):
    base = {
        "id": str(uuid4()), "email": "a@a.com", "nome": "A", "estilo_preferido": None,
        "formato_preferido": None, "objetivos_estudo": None, "cognito_id": "c-1",
        "termos_versao": TERMOS_DE_USO_VERSAO, "tour_concluido": False,
        "termos_aceitos_em": "2026-01-01T00:00:00", "criado_em": "2026-01-01T00:00:00",
        "atualizado_em": "2026-01-01T00:00:00",
    }
    base.update(overrides)
    return base


class TestCriarUsuario:
    def test_com_sucesso_retorna_201(self, client, profile_service):
        profile_service.criar_usuario.return_value = _usuario_dict()

        response = client.post("/profile", json={"email": "a@a.com", "termos_versao": TERMOS_DE_USO_VERSAO})

        assert response.status_code == 201

    def test_quando_service_rejeita_validacao_retorna_400_com_erros(self, client, profile_service):
        from app.core.exceptions import Notification
        profile_service.criar_usuario.side_effect = ValidationNotificationError(
            [Notification(2103, "termos_versao", "Termos desatualizados.")]
        )

        response = client.post("/profile", json={"email": "a@a.com", "termos_versao": "0.1"})

        assert response.status_code == 400
        assert response.json()["errors"][0]["code"] == 2103


class TestBuscarUsuarioPorCognitoId:
    def test_sem_claims_no_token_retorna_401(self, client):
        response = client.get("/profile")

        assert response.status_code == 401

    def test_com_token_valido_retorna_200(self, client_com_token_valido, profile_service):
        profile_service.buscar_usuario_por_cognito_id.return_value = _usuario_dict()

        response = client_com_token_valido.get("/profile")

        assert response.status_code == 200
        profile_service.buscar_usuario_por_cognito_id.assert_called_once_with("cognito-id-123")


class TestAtualizarMeuPerfil:
    def test_com_token_valido_retorna_200(self, client_com_token_valido, profile_service):
        usuario_atual = SimpleNamespace(id=uuid4())
        profile_service.buscar_usuario_por_cognito_id.return_value = usuario_atual
        profile_service.atualizar_usuario_por_id.return_value = _usuario_dict(id=str(usuario_atual.id))

        response = client_com_token_valido.put("/profile", json={"email": "novo@a.com"})

        assert response.status_code == 200
        chamada = profile_service.atualizar_usuario_por_id.call_args
        assert chamada.args[0] == usuario_atual.id
        assert chamada.args[1].email == "novo@a.com"

    def test_sem_claims_no_token_retorna_401(self, client):
        response = client.put("/profile", json={"email": "a@a.com"})

        assert response.status_code == 401


class TestBuscarUsuarioPorId:
    def test_do_proprio_usuario_retorna_200(self, client, profile_service, usuario_id):
        profile_service.buscar_usuario_por_id.return_value = _usuario_dict(id=str(usuario_id))

        response = client.get(f"/profile/{usuario_id}")

        assert response.status_code == 200

    def test_de_outro_usuario_retorna_403(self, client):
        response = client.get(f"/profile/{uuid4()}")

        assert response.status_code == 403

    def test_inexistente_retorna_404(self, client, profile_service, usuario_id):
        profile_service.buscar_usuario_por_id.side_effect = ProfileNotFoundError("Usuário não encontrado.")

        response = client.get(f"/profile/{usuario_id}")

        assert response.status_code == 404
        assert response.json()["error_code"] == 2001


class TestAtualizarUsuarioPorId:
    def test_do_proprio_usuario_retorna_200(self, client, profile_service, usuario_id):
        profile_service.atualizar_usuario_por_id.return_value = _usuario_dict(id=str(usuario_id))

        response = client.put(f"/profile/{usuario_id}", json={"email": "a@a.com"})

        assert response.status_code == 200

    def test_de_outro_usuario_retorna_403(self, client):
        response = client.put(f"/profile/{uuid4()}", json={"email": "a@a.com"})

        assert response.status_code == 403


class TestDeletarUsuarioPorId:
    def test_do_proprio_usuario_retorna_204(self, client, profile_service, usuario_id):
        profile_service.deletar_usuario_por_id.return_value = None

        response = client.delete(f"/profile/{usuario_id}")

        assert response.status_code == 204

    def test_de_outro_usuario_retorna_403(self, client):
        response = client.delete(f"/profile/{uuid4()}")

        assert response.status_code == 403


class TestObterDashboard:
    def test_do_proprio_usuario_retorna_200(self, client, dashboard_service, usuario_id):
        dashboard_service.obter_dashboard_usuario.return_value = DashboardResponse(
            ultimos_flashcards=[], ultimos_resumos=[], ultimos_quizzes=[], documentos_recentes=[],
            total_flashcards=0, total_resumos=0, total_quizzes=0,
        )

        response = client.get(f"/profile/{usuario_id}/dashboard")

        assert response.status_code == 200

    def test_de_outro_usuario_retorna_403(self, client):
        response = client.get(f"/profile/{uuid4()}/dashboard")

        assert response.status_code == 403


class TestSalvarPerfilOnboarding:
    def test_do_proprio_usuario_retorna_200(self, client, profile_service, usuario_id):
        profile_service.atualizar_perfil_onboarding.return_value = _usuario_dict(id=str(usuario_id))

        response = client.post(f"/profile/{usuario_id}/perfil", json={"objetivos_estudo": "Passar no ENEM"})

        assert response.status_code == 200

    def test_de_outro_usuario_retorna_403(self, client):
        response = client.post(f"/profile/{uuid4()}/perfil", json={})

        assert response.status_code == 403
