import logging.config

from app.api.middlewares.request_id_middleware import RequestIdLogFilter
from app.core.config import settings


def configurar_logging() -> None:
    dict_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {"()": RequestIdLogFilter},
        },
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["request_id"],
            },
        },
        "root": {
            "handlers": ["console"],
            "level": settings.log_level,
        },
    }
    logging.config.dictConfig(dict_config)
