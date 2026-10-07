import logging
import uuid

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.api.middlewares.request_id_middleware import (
    HEADER_NAME,
    RequestIdLogFilter,
    RequestIdMiddleware,
    get_request_id,
)


def _build_app():
    async def handler(request):
        return JSONResponse({"request_id_visto_na_rota": get_request_id()})

    app = Starlette(routes=[Route("/", handler)])
    app.add_middleware(RequestIdMiddleware)
    return app


def test_get_request_id_retorna_valor_padrao_fora_de_uma_requisicao():
    assert get_request_id() == "-"


def test_dispatch_gera_novo_uuid_quando_header_nao_e_enviado():
    client = TestClient(_build_app())

    response = client.get("/")

    assert response.status_code == 200
    request_id = response.headers[HEADER_NAME]
    uuid.UUID(request_id)
    assert response.json()["request_id_visto_na_rota"] == request_id


def test_dispatch_reutiliza_request_id_recebido_no_header():
    client = TestClient(_build_app())

    response = client.get("/", headers={HEADER_NAME: "id-fornecido-pelo-cliente"})

    assert response.headers[HEADER_NAME] == "id-fornecido-pelo-cliente"
    assert response.json()["request_id_visto_na_rota"] == "id-fornecido-pelo-cliente"


def test_contexto_e_resetado_apos_a_requisicao():
    client = TestClient(_build_app())
    client.get("/", headers={HEADER_NAME: "id-da-primeira-chamada"})

    assert get_request_id() == "-"


class TestRequestIdLogFilter:
    def test_filter_injeta_request_id_no_log_record_e_retorna_true(self):
        log_filter = RequestIdLogFilter()
        record = logging.LogRecord(
            name="teste", level=logging.INFO, pathname="x", lineno=1,
            msg="mensagem", args=None, exc_info=None,
        )

        resultado = log_filter.filter(record)

        assert resultado is True
        assert record.request_id == "-"
