from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user_id,
    get_document_generator_service,
    get_flashcard_service,
    get_quiz_service,
    get_resumo_service,
)
from app.api.routers.document import (
    documentos_router,
    flashcards_router,
    pastas_router,
    quizzes_router,
    resumos_router,
)
from app.core.exceptions import DocumentNotFoundError


@pytest.fixture
def usuario_id():
    return uuid4()


@pytest.fixture
def document_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def flashcard_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def quiz_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def resumo_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def client(app_factory, usuario_id, document_service, flashcard_service, quiz_service, resumo_service):
    app = app_factory(pastas_router, documentos_router, resumos_router, flashcards_router, quizzes_router)
    app.dependency_overrides[get_current_user_id] = lambda: usuario_id
    app.dependency_overrides[get_document_generator_service] = lambda: document_service
    app.dependency_overrides[get_flashcard_service] = lambda: flashcard_service
    app.dependency_overrides[get_quiz_service] = lambda: quiz_service
    app.dependency_overrides[get_resumo_service] = lambda: resumo_service
    return TestClient(app)


class TestPastas:
    def test_criar_pasta_retorna_201(self, client, document_service):
        document_service.criar_pasta_service.return_value = {"id": str(uuid4()), "nome": "Biologia"}

        response = client.post("/pastas", json={"nome": "Biologia", "pasta_pai_id": None})

        assert response.status_code == 201

    def test_listar_pastas_raiz_do_proprio_usuario_retorna_200(self, client, document_service, usuario_id):
        document_service.listar_pastas_raiz_por_usuario.return_value = []

        response = client.get(f"/pastas/user/{usuario_id}")

        assert response.status_code == 200

    def test_listar_pastas_raiz_de_outro_usuario_retorna_403(self, client):
        response = client.get(f"/pastas/user/{uuid4()}")

        assert response.status_code == 403

    def test_listar_todas_pastas_de_outro_usuario_retorna_403(self, client):
        response = client.get(f"/pastas/user/{uuid4()}/todas")

        assert response.status_code == 403

    def test_listar_todas_pastas_do_proprio_usuario_retorna_200(self, client, document_service, usuario_id):
        document_service.listar_todas_pastas_por_usuario.return_value = []

        response = client.get(f"/pastas/user/{usuario_id}/todas")

        assert response.status_code == 200

    def test_listar_conteudo_pasta_com_sucesso_retorna_200(self, client, document_service):
        document_service.listar_conteudo_pasta.return_value = {
            "subpastas": [], "arquivos": [], "total_arquivos": 0, "pagina_atual": 1, "tem_mais_paginas": False,
        }

        response = client.get(f"/pastas/{uuid4()}/conteudo")

        assert response.status_code == 200

    def test_listar_conteudo_pasta_inexistente_retorna_404_com_error_code(self, client, document_service):
        document_service.listar_conteudo_pasta.side_effect = DocumentNotFoundError("Pasta não encontrada.")

        response = client.get(f"/pastas/{uuid4()}/conteudo")

        assert response.status_code == 404
        assert response.json()["error_code"] == 1001

    def test_atualizar_pasta_com_sucesso_retorna_200(self, client, document_service):
        document_service.atualizar_pasta_nome.return_value = {
            "id": str(uuid4()), "nome": "Novo", "usuario_id": str(uuid4()), "pasta_pai_id": None,
            "criada_em": "2026-01-01T00:00:00",
        }

        response = client.put(f"/pastas/{uuid4()}", data={"nome": "Novo"})

        assert response.status_code == 200

    def test_deletar_pasta_com_sucesso_retorna_204(self, client, document_service):
        document_service.deletar_pasta.return_value = None

        response = client.delete(f"/pastas/{uuid4()}")

        assert response.status_code == 204

    def test_deletar_pasta_inexistente_retorna_404(self, client, document_service):
        document_service.deletar_pasta.side_effect = DocumentNotFoundError("Pasta não encontrada.")

        response = client.delete(f"/pastas/{uuid4()}")

        assert response.status_code == 404


class TestDocumentos:
    def test_upload_com_sucesso_retorna_201(self, client, document_service):
        document_service.salvar_documento.return_value = {"id": str(uuid4())}

        response = client.post(
            "/documentos/upload",
            files={"documento": ("prova.pdf", b"conteudo", "application/pdf")},
            data={"pasta_id": str(uuid4()), "nome_documento": "Prova"},
        )

        assert response.status_code == 201

    def test_obter_url_visualizacao_com_sucesso_retorna_200(self, client, document_service):
        document_service.gerar_pre_signed_url_visualizacao.return_value = "https://s3/url"

        response = client.get(f"/documentos/{uuid4()}/url-visualizacao")

        assert response.status_code == 200
        assert response.json()["url"] == "https://s3/url"

    def test_obter_url_visualizacao_documento_inexistente_retorna_404(self, client, document_service):
        document_service.gerar_pre_signed_url_visualizacao.side_effect = DocumentNotFoundError("Não encontrado.")

        response = client.get(f"/documentos/{uuid4()}/url-visualizacao")

        assert response.status_code == 404

    def test_atualizar_documento_com_sucesso_retorna_200(self, client, document_service):
        document_service.atualizar_documento_nome.return_value = {"id": str(uuid4()), "nome": "Renomeado"}

        response = client.put(f"/documentos/{uuid4()}", data={"nome": "Renomeado"})

        assert response.status_code == 200

    def test_deletar_documento_com_sucesso_retorna_204(self, client, document_service):
        document_service.deletar_documento.return_value = None

        response = client.delete(f"/documentos/{uuid4()}")

        assert response.status_code == 204


class TestResumos:
    def test_gerar_resumo_com_sucesso_retorna_201(self, client, resumo_service):
        resumo_service.gerar_resumo.return_value = {
            "id": str(uuid4()), "documento_id": str(uuid4()), "titulo": "R", "formato": "cornell",
            "nivel_conhecimento": 5, "tom": "formal", "s3_chave": "c", "s3_chave_pdf": None,
            "tokens_utilizados": 1, "modelo_ia": "m", "criado_em": "2026-01-01T00:00:00",
        }

        response = client.post(
            f"/documentos/{uuid4()}/resumos",
            json={"nivel_conhecimento": 5, "formato": "cornell", "tom": "formal"},
        )

        assert response.status_code == 201

    def test_listar_resumos_do_documento_retorna_200(self, resumo_service, client):
        resumo_service.listar_por_documento.return_value = []

        response = client.get(f"/documentos/{uuid4()}/resumos")

        assert response.status_code == 200

    def test_obter_conteudo_resumo_inexistente_retorna_404(self, client, resumo_service):
        resumo_service.obter_conteudo.side_effect = DocumentNotFoundError("Não encontrado.")

        response = client.get(f"/resumos/{uuid4()}/conteudo")

        assert response.status_code == 404

    def test_obter_download_pdf_resumo_com_sucesso_retorna_200(self, client, resumo_service):
        resumo_service.obter_download_url.return_value = "https://s3/resumo.pdf"

        response = client.get(f"/resumos/{uuid4()}/download")

        assert response.status_code == 200

    def test_renomear_resumo_com_sucesso_retorna_200(self, client, resumo_service):
        resumo_service.renomear_resumo.return_value = {
            "id": str(uuid4()), "documento_id": str(uuid4()), "titulo": "Novo", "formato": "cornell",
            "nivel_conhecimento": 5, "tom": "formal", "s3_chave": "c", "s3_chave_pdf": None,
            "tokens_utilizados": 1, "modelo_ia": "m", "criado_em": "2026-01-01T00:00:00",
        }

        response = client.put(f"/resumos/{uuid4()}", json={"titulo": "Novo"})

        assert response.status_code == 200

    def test_deletar_resumo_com_sucesso_retorna_204(self, client, resumo_service):
        resumo_service.deletar_resumo.return_value = None

        response = client.delete(f"/resumos/{uuid4()}")

        assert response.status_code == 204


class TestFlashcards:
    def test_gerar_flashcards_com_sucesso_retorna_201(self, client, flashcard_service):
        flashcard_service.gerar_flashcards.return_value = {
            "id": str(uuid4()), "documento_id": str(uuid4()), "titulo": "F", "s3_chave": "c",
            "tokens_utilizados": 1, "modelo_ia": "m", "criado_em": "2026-01-01T00:00:00",
        }

        response = client.post(f"/documentos/{uuid4()}/flashcards", json={"quantidade": 5, "dificuldade": "facil"})

        assert response.status_code == 201

    def test_listar_flashcards_do_documento_retorna_200(self, client, flashcard_service):
        flashcard_service.listar_por_documento.return_value = []

        response = client.get(f"/documentos/{uuid4()}/flashcards")

        assert response.status_code == 200

    def test_obter_conteudo_flashcard_inexistente_retorna_404(self, client, flashcard_service):
        flashcard_service.obter_conteudo.side_effect = DocumentNotFoundError("Não encontrado.")

        response = client.get(f"/flashcards/{uuid4()}/conteudo")

        assert response.status_code == 404

    def test_renomear_flashcard_com_sucesso_retorna_200(self, client, flashcard_service):
        flashcard_service.renomear_flashcard.return_value = {
            "id": str(uuid4()), "documento_id": str(uuid4()), "titulo": "Novo", "s3_chave": "c",
            "tokens_utilizados": 1, "modelo_ia": "m", "criado_em": "2026-01-01T00:00:00",
        }

        response = client.put(f"/flashcards/{uuid4()}", json={"titulo": "Novo"})

        assert response.status_code == 200

    def test_deletar_flashcard_com_sucesso_retorna_204(self, client, flashcard_service):
        flashcard_service.deletar_flashcard.return_value = None

        response = client.delete(f"/flashcards/{uuid4()}")

        assert response.status_code == 204


class TestQuizzes:
    def test_gerar_quiz_com_sucesso_retorna_201(self, client, quiz_service):
        quiz_service.gerar_quiz.return_value = {
            "id": str(uuid4()), "documento_id": str(uuid4()), "titulo": "Q", "s3_chave": "c",
            "tokens_utilizados": 1, "modelo_ia": "m", "criado_em": "2026-01-01T00:00:00",
        }

        response = client.post(f"/documentos/{uuid4()}/quizzes", json={"quantidade": 5, "dificuldade": "facil"})

        assert response.status_code == 201

    def test_listar_quizzes_do_documento_retorna_200(self, client, quiz_service):
        quiz_service.listar_por_documento.return_value = []

        response = client.get(f"/documentos/{uuid4()}/quizzes")

        assert response.status_code == 200

    def test_obter_conteudo_quiz_inexistente_retorna_404(self, client, quiz_service):
        quiz_service.obter_conteudo.side_effect = DocumentNotFoundError("Não encontrado.")

        response = client.get(f"/quizzes/{uuid4()}/conteudo")

        assert response.status_code == 404

    def test_renomear_quiz_com_sucesso_retorna_200(self, client, quiz_service):
        quiz_service.renomear_quiz.return_value = {
            "id": str(uuid4()), "documento_id": str(uuid4()), "titulo": "Novo", "s3_chave": "c",
            "tokens_utilizados": 1, "modelo_ia": "m", "criado_em": "2026-01-01T00:00:00",
        }

        response = client.put(f"/quizzes/{uuid4()}", json={"titulo": "Novo"})

        assert response.status_code == 200

    def test_deletar_quiz_com_sucesso_retorna_204(self, client, quiz_service):
        quiz_service.deletar_quiz.return_value = None

        response = client.delete(f"/quizzes/{uuid4()}")

        assert response.status_code == 204


class TestBuscaDeDocumentos:
    def test_busca_retorna_200_com_itens_e_paginacao(self, client, document_service, usuario_id):
        document_service.buscar_documentos.return_value = {
            "itens": [{
                "id": str(uuid4()), "nome": "Sono", "pasta_nome": "Semestre 6",
                "pasta_caminho": "Faculdade › Semestre 6", "criado_em": "2026-01-01T00:00:00",
            }],
            "total": 1,
            "tem_mais": False,
        }

        response = client.get("/documentos", params={"q": "sono", "limit": 10, "offset": 5})

        assert response.status_code == 200
        assert response.json()["itens"][0]["pasta_nome"] == "Semestre 6"
        assert response.json()["itens"][0]["pasta_caminho"] == "Faculdade › Semestre 6"
        document_service.buscar_documentos.assert_called_once_with(usuario_id, "sono", 10, 5)

    def test_busca_sem_parametros_usa_padroes(self, client, document_service, usuario_id):
        document_service.buscar_documentos.return_value = {"itens": [], "total": 0, "tem_mais": False}

        response = client.get("/documentos")

        assert response.status_code == 200
        document_service.buscar_documentos.assert_called_once_with(usuario_id, "", 20, 0)

    @pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 51}, {"offset": -1}, {"q": "x" * 101}])
    def test_parametros_invalidos_retornam_422(self, client, params):
        assert client.get("/documentos", params=params).status_code == 422


class TestPdfInline:
    def test_arquivo_do_documento_retorna_pdf_inline(self, client, document_service):
        document_service.obter_arquivo_bytes.return_value = b"%PDF-1.4 conteudo"

        response = client.get(f"/documentos/{uuid4()}/arquivo")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"].startswith("inline")
        assert response.content == b"%PDF-1.4 conteudo"

    def test_arquivo_de_documento_inexistente_retorna_404(self, client, document_service):
        document_service.obter_arquivo_bytes.side_effect = DocumentNotFoundError("Não encontrado.")

        assert client.get(f"/documentos/{uuid4()}/arquivo").status_code == 404

    def test_pdf_do_resumo_retorna_pdf_inline(self, client, resumo_service):
        resumo_service.obter_pdf_bytes.return_value = b"%PDF-1.4 resumo"

        response = client.get(f"/resumos/{uuid4()}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"].startswith("inline")
        assert response.content == b"%PDF-1.4 resumo"
        assert "no-store" in response.headers["cache-control"]

    def test_pdf_de_resumo_inexistente_retorna_404(self, client, resumo_service):
        from app.core.exceptions import ResumoNotFoundError

        resumo_service.obter_pdf_bytes.side_effect = ResumoNotFoundError("Não encontrado.")

        assert client.get(f"/resumos/{uuid4()}/pdf").status_code == 404


class TestHierarquiaDePastas:
    def test_todas_as_pastas_expoem_o_pai_para_montar_a_arvore(self, client, document_service, usuario_id):
        raiz, filha = uuid4(), uuid4()
        document_service.listar_todas_pastas_por_usuario.return_value = [
            {"id": raiz, "nome": "Faculdade", "pasta_pai_id": None, "criada_em": "2026-01-01T00:00:00"},
            {"id": filha, "nome": "Semestre 6", "pasta_pai_id": raiz, "criada_em": "2026-01-02T00:00:00"},
        ]

        response = client.get(f"/pastas/user/{usuario_id}/todas")

        assert response.status_code == 200
        corpo = response.json()
        assert corpo[0]["pasta_pai_id"] is None
        assert corpo[1]["pasta_pai_id"] == str(raiz)


class TestConteudoSomenteVencidos:
    def test_flashcard_repassa_somente_vencidos_ao_service(self, client, flashcard_service):
        flashcard_service.obter_conteudo.side_effect = DocumentNotFoundError("Não encontrado.")
        flashcard_id = uuid4()

        client.get(f"/flashcards/{flashcard_id}/conteudo?somente_vencidos=true")

        assert flashcard_service.obter_conteudo.call_args[0][2] is True

    def test_quiz_repassa_somente_vencidos_ao_service(self, client, quiz_service):
        quiz_service.obter_conteudo.side_effect = DocumentNotFoundError("Não encontrado.")
        quiz_id = uuid4()

        client.get(f"/quizzes/{quiz_id}/conteudo?somente_vencidos=true")

        assert quiz_service.obter_conteudo.call_args[0][2] is True
