import logging
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")

HEADER_NAME = "X-Request-ID"


def get_request_id() -> str:
    return _request_id_ctx_var.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get(HEADER_NAME)
        request_id = incoming or str(uuid.uuid4())
        token = _request_id_ctx_var.set(request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            _request_id_ctx_var.reset(token)
        response.headers[HEADER_NAME] = request_id
        return response


class RequestIdLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
