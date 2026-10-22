from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user_id, get_revisao_service
from app.api.routers.revisao import router
from app.core.exceptions import RevisaoNotFoundError


@pytest.fixture
def usuario_id():
    return uuid4()


@pytest.fixture
def revisao_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def client(app_factory, usuario_id, revisao_service):
    app = app_factory(router)
    app.dependency_overrides[get_current_user_id] = lambda: usuario_id
    app.dependency_overrides[get_revisao_service] = lambda: revisao_service
    return TestClient(app)


def _item_revisao():
    return {
        "id": str(uuid4()), "origem_id": str(uuid4()), "item_ref": "card_001",
        "fator_facilidade": 2.5, "intervalo_atual": 1, "repeticoes": 0,
        "proxima_revisao": datetime.utcnow().isoformat(), "conteudo": None,
    }


def test_buscar_revisoes_hoje_retorna_200(client, revisao_service):
    revisao_service.buscar_daily_mix.return_value = {"cartoes": [], "questoes": [], "total": 0}

    response = client.get("/revisoes/hoje")

    assert response.status_code == 200


def test_buscar_flashcards_pendentes_retorna_200(client, revisao_service):
    revisao_service.buscar_flashcards_pendentes.return_value = [_item_revisao()]

    response = client.get("/revisoes/flashcards")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_buscar_quizzes_pendentes_retorna_200(client, revisao_service):
    revisao_service.buscar_quizzes_pendentes.return_value = []

    response = client.get("/revisoes/quizzes")

    assert response.status_code == 200


def test_buscar_flashcards_todos_retorna_200(client, revisao_service):
    revisao_service.buscar_flashcards_todos.return_value = []

    response = client.get("/revisoes/flashcards/todos")

    assert response.status_code == 200


def test_buscar_quizzes_todos_retorna_200(client, revisao_service):
    revisao_service.buscar_quizzes_todos.return_value = []

    response = client.get("/revisoes/quizzes/todos")

    assert response.status_code == 200


class TestAvaliarCartao:
    def test_com_sucesso_retorna_200(self, client, revisao_service):
        revisao_service.avaliar_cartao.return_value = {
            "id": str(uuid4()), "fator_facilidade": 2.6, "intervalo_atual": 6,
            "repeticoes": 1, "proxima_revisao": datetime.utcnow().isoformat(),
        }

        response = client.put(f"/revisoes/cartoes/{uuid4()}/avaliar", json={"qualidade": 5})

        assert response.status_code == 200

    def test_item_inexistente_retorna_404(self, client, revisao_service):
        revisao_service.avaliar_cartao.side_effect = RevisaoNotFoundError("Item de revisão não encontrado.")

        response = client.put(f"/revisoes/cartoes/{uuid4()}/avaliar", json={"qualidade": 5})

        assert response.status_code == 404
        assert response.json()["error_code"] == 6001


class TestAvaliarQuestao:
    def test_com_sucesso_retorna_200(self, client, revisao_service):
        revisao_service.avaliar_questao.return_value = {
            "id": str(uuid4()), "fator_facilidade": 2.6, "intervalo_atual": 6,
            "repeticoes": 1, "proxima_revisao": datetime.utcnow().isoformat(),
        }

        response = client.put(f"/revisoes/questoes/{uuid4()}/avaliar", json={"qualidade": 4})

        assert response.status_code == 200

    def test_item_inexistente_retorna_404(self, client, revisao_service):
        revisao_service.avaliar_questao.side_effect = RevisaoNotFoundError("Item de revisão não encontrado.")

        response = client.put(f"/revisoes/questoes/{uuid4()}/avaliar", json={"qualidade": 4})

        assert response.status_code == 404
