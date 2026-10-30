import io
from uuid import uuid4

import pytest

from app.core.exceptions import DocumentNotFoundError, QuizNotFoundError
from app.services.QuizService import QuizService


@pytest.fixture
def quiz_repo(mocker):
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
def service(quiz_repo, document_repo, s3_service, bedrock_service):
    return QuizService(quiz_repo, document_repo, s3_service, bedrock_service)


class TestGerarQuiz:
    def test_com_sucesso_gera_e_persiste_quiz(
        self, service, document_repo, s3_service, bedrock_service, quiz_repo, mocker
    ):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": "doc.pdf"}
        s3_service.download_file.return_value = io.BytesIO(b"pdf-bytes")
        bedrock_service.gerar_quiz.return_value = ([{"item_ref": "q_001"}], 100, "modelo-x")
        quiz_repo.criar_quiz_com_questoes.return_value = {"id": uuid4()}

        resultado = service.gerar_quiz(uuid4(), uuid4(), quantidade=5, dificuldade="facil")

        assert "id" in resultado
        bedrock_service.gerar_quiz.assert_called_once_with(b"pdf-bytes", 5, "facil")
        s3_service.upload_json.assert_called_once()

    def test_quando_documento_nao_encontrado_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = None

        with pytest.raises(DocumentNotFoundError):
            service.gerar_quiz(uuid4(), uuid4())

    def test_quando_documento_sem_chave_s3_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": None}

        with pytest.raises(DocumentNotFoundError):
            service.gerar_quiz(uuid4(), uuid4())


def test_listar_por_documento_delega_para_repositorio(service, quiz_repo):
    quiz_repo.listar_por_documento.return_value = [{"id": uuid4()}]

    resultado = service.listar_por_documento(uuid4(), uuid4())

    assert len(resultado) == 1


class TestObterConteudo:
    def test_com_sucesso_enriquece_questoes_com_conteudo_do_s3(self, service, quiz_repo, s3_service):
        quiz_id = uuid4()
        quiz_repo.buscar_por_id.return_value = {"id": quiz_id, "titulo": "Q", "s3_chave": "chave.json"}
        quiz_repo.listar_questoes_por_quiz.return_value = [{"item_ref": "q_001"}]
        s3_service.download_json.return_value = [{"item_ref": "q_001", "pergunta": "P?"}]

        resultado = service.obter_conteudo(quiz_id, uuid4())

        assert resultado["questoes"][0]["conteudo"]["pergunta"] == "P?"

    def test_quando_quiz_nao_encontrado_levanta_erro(self, service, quiz_repo):
        quiz_repo.buscar_por_id.return_value = None

        with pytest.raises(QuizNotFoundError):
            service.obter_conteudo(uuid4(), uuid4())

    def test_quando_s3_falha_usa_lista_vazia_como_fallback(self, service, quiz_repo, s3_service):
        quiz_repo.buscar_por_id.return_value = {"id": uuid4(), "titulo": "Q", "s3_chave": "chave.json"}
        quiz_repo.listar_questoes_por_quiz.return_value = [{"item_ref": "q_001"}]
        s3_service.download_json.side_effect = Exception("s3 indisponível")

        resultado = service.obter_conteudo(uuid4(), uuid4())

        assert resultado["questoes"][0]["conteudo"] is None


class TestRenomearQuiz:
    def test_com_sucesso_retorna_quiz_atualizado(self, service, quiz_repo):
        quiz_repo.atualizar_titulo.return_value = {"titulo": "Novo"}

        resultado = service.renomear_quiz(uuid4(), uuid4(), "Novo")

        assert resultado["titulo"] == "Novo"

    def test_quando_nao_encontrado_levanta_erro(self, service, quiz_repo):
        quiz_repo.atualizar_titulo.return_value = None

        with pytest.raises(QuizNotFoundError):
            service.renomear_quiz(uuid4(), uuid4(), "Novo")


class TestDeletarQuiz:
    def test_com_sucesso_nao_levanta_erro(self, service, quiz_repo):
        quiz_repo.deletar.return_value = True

        service.deletar_quiz(uuid4(), uuid4())

    def test_quando_nao_encontrado_levanta_erro(self, service, quiz_repo):
        quiz_repo.deletar.return_value = False

        with pytest.raises(QuizNotFoundError):
            service.deletar_quiz(uuid4(), uuid4())


class TestObterConteudoSomenteVencidos:
    def test_repasse_do_filtro_ao_repositorio(self, service, quiz_repo):
        quiz_id = uuid4()
        usuario_id = uuid4()
        quiz_repo.buscar_por_id.return_value = {"id": quiz_id, "titulo": "Q", "s3_chave": "chave.json"}
        quiz_repo.listar_questoes_por_quiz.return_value = []

        service.obter_conteudo(quiz_id, usuario_id, somente_vencidos=True)

        quiz_repo.listar_questoes_por_quiz.assert_called_once_with(quiz_id, usuario_id, True)
