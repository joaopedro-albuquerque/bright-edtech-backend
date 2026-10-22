from app.api.middlewares.request_id_middleware import RequestIdLogFilter
from app.core.config import settings
from app.core.logging_config import configurar_logging


def test_configurar_logging_aplica_dictconfig_com_formatter_json_e_filtro_de_request_id(mocker):
    dict_config_spy = mocker.patch("app.core.logging_config.logging.config.dictConfig")

    configurar_logging()

    dict_config_spy.assert_called_once()
    config_usado = dict_config_spy.call_args[0][0]

    assert config_usado["filters"]["request_id"]["()"] is RequestIdLogFilter
    assert config_usado["formatters"]["json"]["()"] == "pythonjsonlogger.jsonlogger.JsonFormatter"
    assert config_usado["handlers"]["console"]["filters"] == ["request_id"]
    assert config_usado["handlers"]["console"]["formatter"] == "json"
    assert config_usado["root"]["handlers"] == ["console"]
    assert config_usado["root"]["level"] == settings.log_level
