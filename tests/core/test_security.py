import pytest
from jwt.exceptions import PyJWTError

from app.core import security


@pytest.fixture(autouse=True)
def reset_jwk_client_singleton():
    security._jwk_client = None
    yield
    security._jwk_client = None


def test_obter_jwk_client_cria_uma_unica_instancia_reutilizada(mocker):
    mock_client_cls = mocker.patch("app.core.security.PyJWKClient")

    cliente1 = security._obter_jwk_client()
    cliente2 = security._obter_jwk_client()

    assert cliente1 is cliente2
    mock_client_cls.assert_called_once_with(security._JWKS_URL)


def test_verificar_token_cognito_retorna_claims_para_id_token_valido(mocker):
    mock_obter_client = mocker.patch("app.core.security._obter_jwk_client")
    mock_obter_client.return_value.get_signing_key_from_jwt.return_value.key = "chave-publica"
    claims = {"sub": "user-123", "token_use": "id", "aud": security.COGNITO_CLIENT_ID}
    mocker.patch("app.core.security.jwt_decode", return_value=claims)

    resultado = security.verificar_token_cognito("token-fake")

    assert resultado == claims


def test_verificar_token_cognito_retorna_claims_para_access_token_valido(mocker):
    mocker.patch("app.core.security._obter_jwk_client")
    claims = {"sub": "user-123", "token_use": "access", "client_id": security.COGNITO_CLIENT_ID}
    mocker.patch("app.core.security.jwt_decode", return_value=claims)

    resultado = security.verificar_token_cognito("token-fake")

    assert resultado == claims


def test_verificar_token_cognito_levanta_erro_quando_client_id_nao_corresponde(mocker):
    mocker.patch("app.core.security._obter_jwk_client")
    claims = {"sub": "user-123", "token_use": "id", "aud": "outro-client-id-qualquer"}
    mocker.patch("app.core.security.jwt_decode", return_value=claims)

    with pytest.raises(PyJWTError, match="não pertence ao client"):
        security.verificar_token_cognito("token-fake")


def test_verificar_token_cognito_propaga_erro_quando_assinatura_e_invalida(mocker):
    mocker.patch("app.core.security._obter_jwk_client")
    mocker.patch("app.core.security.jwt_decode", side_effect=PyJWTError("assinatura inválida"))

    with pytest.raises(PyJWTError, match="assinatura inválida"):
        security.verificar_token_cognito("token-fake")


def test_verificar_token_cognito_propaga_erro_quando_jwks_nao_encontra_chave(mocker):
    mock_obter_client = mocker.patch("app.core.security._obter_jwk_client")
    mock_obter_client.return_value.get_signing_key_from_jwt.side_effect = PyJWTError("kid não encontrado")

    with pytest.raises(PyJWTError, match="kid não encontrado"):
        security.verificar_token_cognito("token-fake")
