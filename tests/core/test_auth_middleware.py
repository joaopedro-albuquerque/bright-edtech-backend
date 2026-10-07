from jwt.exceptions import PyJWTError
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.auth_middleware import AuthMiddleware


def _build_app():
    async def handler(request):
        claims = getattr(request.state, "token_claims", None)
        return JSONResponse({"token_claims": claims})

    app = Starlette(routes=[
        Route("/", handler),
        Route("/privada", handler),
        Route("/profile", handler, methods=["POST"]),
    ])
    app.add_middleware(AuthMiddleware)
    return app


def test_requisicao_sem_header_authorization_retorna_401(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    client = TestClient(_build_app())

    response = client.get("/rota-privada")

    assert response.status_code == 401
    assert "Authorization: Bearer" in response.json()["detail"]


def test_requisicao_com_header_sem_prefixo_bearer_retorna_401(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    client = TestClient(_build_app())

    response = client.get("/rota-privada", headers={"authorization": "token-sem-prefixo"})

    assert response.status_code == 401


def test_require_auth_false_libera_requisicao_sem_validar_token(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", False)
    verificar_spy = mocker.patch("app.core.auth_middleware.verificar_token_cognito")
    client = TestClient(_build_app())

    response = client.get("/rota-privada")

    assert response.status_code == 404
    verificar_spy.assert_not_called()


def test_metodo_options_e_liberado_sem_token(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    verificar_spy = mocker.patch("app.core.auth_middleware.verificar_token_cognito")
    client = TestClient(_build_app())

    response = client.options("/qualquer-rota")

    assert response.status_code != 401
    verificar_spy.assert_not_called()


def test_caminho_publico_e_liberado_sem_token(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    verificar_spy = mocker.patch("app.core.auth_middleware.verificar_token_cognito")
    client = TestClient(_build_app())

    response = client.get("/")

    assert response.status_code == 200
    verificar_spy.assert_not_called()


def test_post_profile_e_liberado_sem_token(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    verificar_spy = mocker.patch("app.core.auth_middleware.verificar_token_cognito")
    client = TestClient(_build_app())

    response = client.post("/profile")

    assert response.status_code == 200
    verificar_spy.assert_not_called()


def test_token_invalido_retorna_401_e_loga_warning(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    mocker.patch(
        "app.core.auth_middleware.verificar_token_cognito",
        side_effect=PyJWTError("token expirado"),
    )
    warning_spy = mocker.patch("app.core.auth_middleware.logger.warning")
    client = TestClient(_build_app())

    response = client.get("/rota-privada", headers={"authorization": "Bearer token-invalido"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Token de acesso inválido ou expirado."
    warning_spy.assert_called_once()


def test_erro_inesperado_na_validacao_retorna_401_e_loga_com_traceback(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    mocker.patch(
        "app.core.auth_middleware.verificar_token_cognito",
        side_effect=RuntimeError("falha de rede ao buscar jwks"),
    )
    warning_spy = mocker.patch("app.core.auth_middleware.logger.warning")
    client = TestClient(_build_app())

    response = client.get("/rota-privada", headers={"authorization": "Bearer token-qualquer"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Não foi possível validar o token de acesso."
    warning_spy.assert_called_once_with("Falha inesperada ao validar token de acesso.", exc_info=True)


def test_token_valido_libera_requisicao_e_propaga_claims(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    claims = {"sub": "user-123"}
    mocker.patch("app.core.auth_middleware.verificar_token_cognito", return_value=claims)
    client = TestClient(_build_app())

    response = client.get("/privada", headers={"authorization": "Bearer token-valido"})

    assert response.status_code == 200
    assert response.json()["token_claims"] == claims


def test_bearer_prefixo_case_insensitive_e_aceito(mocker):
    mocker.patch("app.core.auth_middleware.REQUIRE_AUTH", True)
    claims = {"sub": "user-123"}
    mocker.patch("app.core.auth_middleware.verificar_token_cognito", return_value=claims)
    client = TestClient(_build_app())

    response = client.get("/privada", headers={"authorization": "BEARER token-valido"})

    assert response.status_code == 200
