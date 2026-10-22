from fastapi.testclient import TestClient

from app.main import app


def test_health_check_retorna_online_sem_autenticacao():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "online", "mensagem": "Servidor FastAPI rodando!"}


def test_health_check_inclui_header_de_request_id():
    client = TestClient(app)

    response = client.get("/")

    assert "x-request-id" in response.headers


def test_rota_protegida_sem_token_retorna_401():
    client = TestClient(app)

    response = client.get("/profile/" + "0" * 8 + "-0000-0000-0000-000000000000")

    assert response.status_code == 401
