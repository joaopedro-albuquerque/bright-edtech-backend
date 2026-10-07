from uuid import uuid4

import pytest

from app.core.exceptions import ResumoDatabaseError
from app.repositories.ResumoRepository import ResumoRepository


@pytest.fixture
def repo(mock_conn):
    return ResumoRepository(mock_conn)


class TestCriar:
    def test_criar_com_sucesso_retorna_dict_e_commita(self, repo, mock_cursor, mock_conn):
        resumo_id = uuid4()
        mock_cursor.fetchone.return_value = {"id": resumo_id, "titulo": "Resumo"}

        resultado = repo.criar(
            uuid4(), uuid4(), "Resumo", "cornell", 5, "formal", "chave", 100, "modelo-x", "chave.pdf"
        )

        assert resultado["id"] == resumo_id
        mock_conn.commit.assert_called_once()

    def test_criar_quando_returning_vazio_levanta_erro_e_faz_rollback(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        with pytest.raises(ResumoDatabaseError):
            repo.criar(uuid4(), uuid4(), "T", "f", 1, "tom", "c", 1, "m")

        mock_conn.rollback.assert_called_once()

    def test_criar_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(ResumoDatabaseError):
            repo.criar(uuid4(), uuid4(), "T", "f", 1, "tom", "c", 1, "m")


class TestListarPorDocumento:
    def test_listar_por_documento_retorna_lista(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = [{"id": uuid4(), "titulo": "A"}]

        resultado = repo.listar_por_documento(uuid4(), uuid4())

        assert len(resultado) == 1

    def test_listar_por_documento_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(ResumoDatabaseError):
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

        with pytest.raises(ResumoDatabaseError):
            repo.buscar_por_id(uuid4(), uuid4())


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

        with pytest.raises(ResumoDatabaseError):
            repo.atualizar_titulo(uuid4(), uuid4(), "Novo")


class TestAtualizarS3ChavePdf:
    def test_atualizar_s3_chave_pdf_com_sucesso(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = {"id": uuid4(), "s3_chave_pdf": "nova.pdf"}

        resultado = repo.atualizar_s3_chave_pdf(uuid4(), uuid4(), "nova.pdf")

        assert resultado["s3_chave_pdf"] == "nova.pdf"
        mock_conn.commit.assert_called_once()

    def test_atualizar_s3_chave_pdf_retorna_none_quando_nao_encontrado(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        resultado = repo.atualizar_s3_chave_pdf(uuid4(), uuid4(), "nova.pdf")

        assert resultado is None
        mock_conn.rollback.assert_called_once()

    def test_atualizar_s3_chave_pdf_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(ResumoDatabaseError):
            repo.atualizar_s3_chave_pdf(uuid4(), uuid4(), "nova.pdf")


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

        with pytest.raises(ResumoDatabaseError):
            repo.deletar(uuid4(), uuid4())

        mock_conn.rollback.assert_called_once()
