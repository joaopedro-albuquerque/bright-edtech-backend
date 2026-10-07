import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.middlewares.request_id_middleware import get_request_id
from app.core.exceptions import AppException, ValidationNotificationError

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = get_request_id()
    nivel = logging.CRITICAL if exc.http_status >= 500 else logging.ERROR
    logger.log(nivel, exc.message, exc_info=exc)
    return JSONResponse(
        status_code=exc.http_status,
        content={"error_code": exc.code, "detail": exc.message, "request_id": request_id},
    )


async def validation_notification_handler(request: Request, exc: ValidationNotificationError) -> JSONResponse:
    request_id = get_request_id()
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error_code": exc.code,
            "detail": exc.message,
            "errors": [
                {"code": n.code, "field": n.field, "message": n.message}
                for n in exc.notifications
            ],
            "request_id": request_id,
        },
    )


async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = get_request_id()
    return JSONResponse(
        status_code=422,
        content={
            "error_code": 9422,
            "detail": "Erro de validação dos dados enviados.",
            "errors": jsonable_encoder(exc.errors()),
            "request_id": request_id,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id()
    logger.critical("Erro não tratado.", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error_code": 9999, "detail": "Erro interno inesperado.", "request_id": request_id},
    )
