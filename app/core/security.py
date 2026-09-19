import os

from jwt import PyJWKClient
from jwt import decode as jwt_decode
from jwt.exceptions import PyJWTError

COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_0AobHYnIw")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "25n05802scoi61pnlptah22ij9")
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")

_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
_JWKS_URL = f"{_ISSUER}/.well-known/jwks.json"

_jwk_client: PyJWKClient | None = None


def _obter_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(_JWKS_URL)
    return _jwk_client


def verificar_token_cognito(token: str) -> dict:
    """
    Valida assinatura (RS256, via JWKS do Cognito), emissor e expiração de um
    token JWT emitido pelo User Pool configurado. Levanta PyJWTError se o
    token for inválido, expirado ou não pertencer a este User Pool/Client.
    """
    signing_key = _obter_jwk_client().get_signing_key_from_jwt(token)

    claims = jwt_decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=_ISSUER,
        options={"verify_aud": False},
    )

    # id_token carrega o client id em "aud"; access_token carrega em "client_id".
    token_use = claims.get("token_use")
    client_id = claims.get("aud") if token_use == "id" else claims.get("client_id")
    if client_id != COGNITO_CLIENT_ID:
        raise PyJWTError("Token não pertence ao client configurado para esta API.")

    return claims
