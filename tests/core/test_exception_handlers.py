import logging

import pytest
from fastapi.exceptions import RequestValidationError

from app.api.middlewares.request_id_middleware import _request_id_ctx_var
from app.core.exception_handlers import (
    app_exception_handler,
    request_validation_error_handler,
    unhandled_exception_handler,
    validation_notification_handler,
)
from app.core.exceptions import DocumentNotFoundError, Notification, ValidationNotificationError


@pytest.fixture(autouse=True)
def _reset_request_id():
    token = _request_id_ctx_var.set("req-teste-123")
    yield
    _request_id_ctx_var.reset(token)


@pytest.mark.asyncio
async def test_app_exception_handler_retorna_corpo_e_status_do_erro_de_dominio(mocker):
    log_spy = mocker.patch("app.core.exception_handlers.logger.log")
    exc = DocumentNotFoundError("Documento não encontrado.")

    response = await app_exception_handler(None, exc)

    assert response.status_code == 404
    body = response.body.decode()
    assert '"error_code":1001' in body
    assert '"detail":"Documento não encontrado."' in body
    assert '"request_id":"req-teste-123"' in body
    log_spy.assert_called_once_with(logging.ERROR, exc.message, exc_info=exc)


@pytest.mark.asyncio
async def test_app_exception_handler_loga_critical_quando_status_e_500_ou_mais(mocker):
    log_spy = mocker.patch("app.core.exception_handlers.logger.log")
    exc = DocumentNotFoundError("não encontrado")
    exc.http_status = 500

    await app_exception_handler(None, exc)

    log_spy.assert_called_once_with(logging.CRITICAL, exc.message, exc_info=exc)


@pytest.mark.asyncio
async def test_validation_notification_handler_retorna_lista_de_erros_e_status_400():
    exc = ValidationNotificationError(
        [
            Notification(2101, "estilo_preferido", "Estilo inválido."),
            Notification(2102, "formato_preferido", "Formato inválido."),
        ]
    )

    response = await validation_notification_handler(None, exc)

    assert response.status_code == 400
    body = response.body.decode()
    assert '"error_code":9400' in body
    assert '"code":2101' in body
    assert '"field":"estilo_preferido"' in body
    assert '"code":2102' in body
    assert '"request_id":"req-teste-123"' in body


@pytest.mark.asyncio
async def test_request_validation_error_handler_retorna_422_com_erros_do_pydantic():
    exc = RequestValidationError(
        errors=[{"loc": ("body", "email"), "msg": "campo obrigatório", "type": "missing"}]
    )

    response = await request_validation_error_handler(None, exc)

    assert response.status_code == 422
    body = response.body.decode()
    assert '"error_code":9422' in body
    assert "campo obrigat" in body
    assert '"request_id":"req-teste-123"' in body


@pytest.mark.asyncio
async def test_unhandled_exception_handler_retorna_500_opaco_sem_vazar_detalhe(mocker):
    critical_spy = mocker.patch("app.core.exception_handlers.logger.critical")
    exc = RuntimeError("detalhe interno sensível de banco de dados")

    response = await unhandled_exception_handler(None, exc)

    assert response.status_code == 500
    body = response.body.decode()
    assert '"error_code":9999' in body
    assert "detalhe interno sens" not in body
    assert '"request_id":"req-teste-123"' in body
    critical_spy.assert_called_once_with("Erro não tratado.", exc_info=exc)
