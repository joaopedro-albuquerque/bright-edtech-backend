from uuid import uuid4

import pytest

from app.core.exceptions import DocumentNotFoundError, FlashcardNotFoundError
from app.services.FlashcardService import FlashcardService


@pytest.fixture
def flashcard_repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def document_repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def s3_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def bedrock_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def service(flashcard_repo, document_repo, s3_service, bedrock_service):
    return FlashcardService(flashcard_repo, document_repo, s3_service, bedrock_service)


class TestGerarFlashcards:
    def test_com_sucesso_gera_e_persiste_flashcards(
        self, service, document_repo, s3_service, bedrock_service, flashcard_repo, mocker
    ):
        mocker.patch("app.services.FlashcardService.extrair_texto_do_pdf", return_value="texto extraído")
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": "doc.pdf"}
        s3_service.download_file.return_value = b"pdf-bytes"
        bedrock_service.gerar_flashcards.return_value = (
            [{"item_ref": "card_001"}], 100, "modelo-x",
        )
        flashcard_repo.criar_flashcard_com_cartoes.return_value = {"id": uuid4()}

        resultado = service.gerar_flashcards(uuid4(), uuid4(), quantidade=5, dificuldade="facil")

        assert "id" in resultado
        s3_service.upload_json.assert_called_once()

    def test_quando_documento_nao_encontrado_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = None

        with pytest.raises(DocumentNotFoundError):
            service.gerar_flashcards(uuid4(), uuid4())

    def test_quando_documento_sem_chave_s3_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": None}

        with pytest.raises(DocumentNotFoundError):
            service.gerar_flashcards(uuid4(), uuid4())


def test_listar_por_documento_delega_para_repositorio(service, flashcard_repo):
    flashcard_repo.listar_por_documento.return_value = [{"id": uuid4()}]

    resultado = service.listar_por_documento(uuid4(), uuid4())

    assert len(resultado) == 1


class TestObterConteudo:
    def test_com_sucesso_enriquece_cartoes_com_conteudo_do_s3(self, service, flashcard_repo, s3_service):
        flashcard_id = uuid4()
        flashcard_repo.buscar_por_id.return_value = {"id": flashcard_id, "titulo": "F", "s3_chave": "chave.json"}
        flashcard_repo.listar_cartoes_por_flashcard.return_value = [{"item_ref": "card_001"}]
        s3_service.download_json.return_value = [{"item_ref": "card_001", "pergunta": "P?"}]

        resultado = service.obter_conteudo(flashcard_id, uuid4())

        assert resultado["cartoes"][0]["conteudo"]["pergunta"] == "P?"

    def test_quando_flashcard_nao_encontrado_levanta_erro(self, service, flashcard_repo):
        flashcard_repo.buscar_por_id.return_value = None

        with pytest.raises(FlashcardNotFoundError):
            service.obter_conteudo(uuid4(), uuid4())

    def test_quando_s3_falha_usa_lista_vazia_como_fallback(self, service, flashcard_repo, s3_service):
        flashcard_repo.buscar_por_id.return_value = {"id": uuid4(), "titulo": "F", "s3_chave": "chave.json"}
        flashcard_repo.listar_cartoes_por_flashcard.return_value = [{"item_ref": "card_001"}]
        s3_service.download_json.side_effect = Exception("s3 indisponível")

        resultado = service.obter_conteudo(uuid4(), uuid4())

        assert resultado["cartoes"][0]["conteudo"] is None


class TestRenomearFlashcard:
    def test_com_sucesso_retorna_flashcard_atualizado(self, service, flashcard_repo):
        flashcard_repo.atualizar_titulo.return_value = {"titulo": "Novo"}

        resultado = service.renomear_flashcard(uuid4(), uuid4(), "Novo")

        assert resultado["titulo"] == "Novo"

    def test_quando_nao_encontrado_levanta_erro(self, service, flashcard_repo):
        flashcard_repo.atualizar_titulo.return_value = None

        with pytest.raises(FlashcardNotFoundError):
            service.renomear_flashcard(uuid4(), uuid4(), "Novo")


class TestDeletarFlashcard:
    def test_com_sucesso_nao_levanta_erro(self, service, flashcard_repo):
        flashcard_repo.deletar.return_value = True

        service.deletar_flashcard(uuid4(), uuid4())

    def test_quando_nao_encontrado_levanta_erro(self, service, flashcard_repo):
        flashcard_repo.deletar.return_value = False

        with pytest.raises(FlashcardNotFoundError):
            service.deletar_flashcard(uuid4(), uuid4())
