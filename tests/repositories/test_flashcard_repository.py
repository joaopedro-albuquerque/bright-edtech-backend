from uuid import uuid4

import pytest

from app.core.exceptions import FlashcardDatabaseError
from app.repositories.FlashcardRepository import FlashcardRepository


@pytest.fixture
def repo(mock_conn):
    return FlashcardRepository(mock_conn)


class TestCriarFlashcardComCartoes:
    def test_criar_com_sucesso_insere_cartoes_e_commita(self, repo, mock_cursor, mock_conn, mocker):
        flashcard_id = uuid4()
        mock_cursor.fetchone.return_value = {"id": flashcard_id, "titulo": "Flashcards"}
        execute_values_spy = mocker.patch("app.repositories.FlashcardRepository.psycopg2.extras.execute_values")

        resultado = repo.criar_flashcard_com_cartoes(
            uuid4(), uuid4(), "Flashcards", "chave", 100, "modelo-x", ["card_001", "card_002"]
        )

        assert resultado["id"] == flashcard_id
        execute_values_spy.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_criar_quando_returning_vazio_levanta_erro_e_faz_rollback(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        with pytest.raises(FlashcardDatabaseError):
            repo.criar_flashcard_com_cartoes(uuid4(), uuid4(), "T", "c", 1, "m", [])

        mock_conn.rollback.assert_called_once()

    def test_criar_quando_banco_falha_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(FlashcardDatabaseError):
            repo.criar_flashcard_com_cartoes(uuid4(), uuid4(), "T", "c", 1, "m", [])

        mock_conn.rollback.assert_called_once()


class TestListarPorDocumento:
    def test_listar_por_documento_retorna_lista(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = [{"id": uuid4(), "titulo": "A"}]

        resultado = repo.listar_por_documento(uuid4(), uuid4())

        assert len(resultado) == 1

    def test_listar_por_documento_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(FlashcardDatabaseError):
            repo.listar_por_documento(uuid4(), uuid4())


class TestBuscarPorId:
    def test_buscar_por_id_retorna_dict_quando_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = {"id": uuid4(), "titulo": "A"}

        resultado = repo.buscar_por_id(uuid4(), uuid4())

        assert resultado["titulo"] == "A"

    def test_buscar_por_id_retorna_none_quando_nao_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = None

        resultado = repo.buscar_por_id(uuid4(), uuid4())

        assert resultado is None

    def test_buscar_por_id_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(FlashcardDatabaseError):
            repo.buscar_por_id(uuid4(), uuid4())


class TestListarCartoesPorFlashcard:
    def test_listar_cartoes_retorna_lista(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = [{"id": uuid4(), "item_ref": "card_001"}]

        resultado = repo.listar_cartoes_por_flashcard(uuid4(), uuid4())

        assert len(resultado) == 1

    def test_listar_cartoes_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(FlashcardDatabaseError):
            repo.listar_cartoes_por_flashcard(uuid4(), uuid4())


class TestAtualizarTitulo:
    def test_atualizar_titulo_com_sucesso(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = {"id": uuid4(), "titulo": "Novo"}

        resultado = repo.atualizar_titulo(uuid4(), uuid4(), "Novo")

        assert resultado["titulo"] == "Novo"
        mock_conn.commit.assert_called_once()

    def test_atualizar_titulo_retorna_none_quando_nao_encontrado(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        resultado = repo.atualizar_titulo(uuid4(), uuid4(), "Novo")

        assert resultado is None
        mock_conn.rollback.assert_called_once()

    def test_atualizar_titulo_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(FlashcardDatabaseError):
            repo.atualizar_titulo(uuid4(), uuid4(), "Novo")


class TestDeletar:
    def test_deletar_retorna_true_quando_deletado(self, repo, mock_cursor, mock_conn):
        mock_cursor.rowcount = 1

        resultado = repo.deletar(uuid4(), uuid4())

        assert resultado is True
        mock_conn.commit.assert_called_once()

    def test_deletar_retorna_false_quando_nao_encontrado(self, repo, mock_cursor):
        mock_cursor.rowcount = 0

        resultado = repo.deletar(uuid4(), uuid4())

        assert resultado is False

    def test_deletar_quando_banco_falha_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(FlashcardDatabaseError):
            repo.deletar(uuid4(), uuid4())

        mock_conn.rollback.assert_called_once()
