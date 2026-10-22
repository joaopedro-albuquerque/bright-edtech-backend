import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.exception_handlers import (
    app_exception_handler,
    request_validation_error_handler,
    unhandled_exception_handler,
    validation_notification_handler,
)
from app.core.exceptions import AppException, ValidationNotificationError


def build_test_app(*routers):
    app = FastAPI()
    for router in routers:
        app.include_router(router)
    app.add_exception_handler(ValidationNotificationError, validation_notification_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    return app


@pytest.fixture
def app_factory():
    return build_test_app
