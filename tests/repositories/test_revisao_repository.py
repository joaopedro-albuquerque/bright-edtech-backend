from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import RevisaoDatabaseError
from app.repositories.RevisaoRepository import RevisaoRepository, _validar_tabela


@pytest.fixture
def repo(mock_conn):
    return RevisaoRepository(mock_conn)


@pytest.mark.parametrize("tabela", ["cartoes", "questoes"])
def test_validar_tabela_aceita_tabelas_permitidas(tabela):
    _validar_tabela(tabela)


def test_validar_tabela_rejeita_tabela_desconhecida():
    with pytest.raises(ValueError, match="Tabela de revisão inválida"):
        _validar_tabela("tabela_inexistente")


class TestBuscarPendentesHoje:
    def test_retorna_lista_quando_tabela_valida(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = [{"id": uuid4()}]

        resultado = repo.buscar_pendentes_hoje(uuid4(), "cartoes")

        assert len(resultado) == 1

    def test_levanta_value_error_quando_tabela_invalida(self, repo):
        with pytest.raises(ValueError):
            repo.buscar_pendentes_hoje(uuid4(), "tabela_invalida")

    def test_quando_banco_falha_levanta_revisao_database_error(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(RevisaoDatabaseError):
            repo.buscar_pendentes_hoje(uuid4(), "cartoes")


class TestBuscarTodos:
    def test_retorna_lista_quando_tabela_valida(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = [{"id": uuid4()}, {"id": uuid4()}]

        resultado = repo.buscar_todos(uuid4(), "questoes")

        assert len(resultado) == 2

    def test_levanta_value_error_quando_tabela_invalida(self, repo):
        with pytest.raises(ValueError):
            repo.buscar_todos(uuid4(), "tabela_invalida")

    def test_quando_banco_falha_levanta_revisao_database_error(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(RevisaoDatabaseError):
            repo.buscar_todos(uuid4(), "questoes")


class TestBuscarPorId:
    def test_retorna_dict_quando_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = {"id": uuid4(), "fator_facilidade": 2.5}

        resultado = repo.buscar_por_id(uuid4(), uuid4(), "cartoes")

        assert resultado["fator_facilidade"] == 2.5

    def test_retorna_none_quando_nao_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = None

        resultado = repo.buscar_por_id(uuid4(), uuid4(), "cartoes")

        assert resultado is None

    def test_levanta_value_error_quando_tabela_invalida(self, repo):
        with pytest.raises(ValueError):
            repo.buscar_por_id(uuid4(), uuid4(), "tabela_invalida")

    def test_quando_banco_falha_levanta_revisao_database_error(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(RevisaoDatabaseError):
            repo.buscar_por_id(uuid4(), uuid4(), "cartoes")


class TestAtualizarEstado:
    def _kwargs(self, **overrides):
        kwargs = dict(
            item_id=uuid4(), usuario_id=uuid4(), tabela="cartoes",
            fator_facilidade=2.6, intervalo_atual=6, repeticoes=2,
            proxima_revisao=datetime.utcnow(),
        )
        kwargs.update(overrides)
        return kwargs

    def test_atualizar_estado_com_sucesso(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = {"id": uuid4(), "fator_facilidade": 2.6}

        resultado = repo.atualizar_estado(**self._kwargs())

        assert resultado["fator_facilidade"] == 2.6
        mock_conn.commit.assert_called_once()

    def test_atualizar_estado_retorna_none_quando_nao_encontrado(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        resultado = repo.atualizar_estado(**self._kwargs())

        assert resultado is None
        mock_conn.rollback.assert_called_once()

    def test_atualizar_estado_levanta_value_error_quando_tabela_invalida(self, repo):
        with pytest.raises(ValueError):
            repo.atualizar_estado(**self._kwargs(tabela="tabela_invalida"))

    def test_atualizar_estado_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(RevisaoDatabaseError):
            repo.atualizar_estado(**self._kwargs())
