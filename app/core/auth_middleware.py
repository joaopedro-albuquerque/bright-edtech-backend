import logging
import os

from jwt.exceptions import PyJWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.security import verificar_token_cognito

logger = logging.getLogger(__name__)

REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "true").lower() == "true"

CAMINHOS_PUBLICOS = {"/", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware global que exige um Bearer token válido do Cognito em toda
    requisição, antes que ela alcance qualquer rota. Isso evita que a API
    fique acessível sem autenticação, independentemente de a rota exigir
    ou não o cabeçalho X-User-Id.

    Requisições de preflight (OPTIONS) e caminhos públicos (health-check,
    documentação automática do FastAPI) são liberados sem token.
    """

    async def dispatch(self, request: Request, call_next):
        if not REQUIRE_AUTH:
            return await call_next(request)

        if request.method == "OPTIONS" or request.url.path in CAMINHOS_PUBLICOS:
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Cabeçalho 'Authorization: Bearer <token>' é obrigatório."},
            )

        token = auth_header.split(" ", 1)[1].strip()
        try:
            claims = verificar_token_cognito(token)
        except PyJWTError as exc:
            logger.warning(f"Rejeitando requisição com token inválido: {exc}")
            return JSONResponse(status_code=401, content={"detail": "Token de acesso inválido ou expirado."})
        except Exception:
            logger.warning("Falha inesperada ao validar token de acesso.", exc_info=True)
            return JSONResponse(status_code=401, content={"detail": "Não foi possível validar o token de acesso."})

        request.state.token_claims = claims
        return await call_next(request)
