from uuid import uuid4

import pytest

from app.core.exceptions import DocumentDatabaseError
from app.repositories.DocumentRepository import DocumentRepository


@pytest.fixture
def repo(mock_conn):
    return DocumentRepository(mock_conn)


class TestCriarPasta:
    def test_criar_pasta_com_sucesso_retorna_dict_e_commita(self, repo, mock_conn, mock_cursor):
        usuario_id, pasta_id = uuid4(), uuid4()
        mock_cursor.fetchone.return_value = {"id": pasta_id, "usuario_id": usuario_id, "nome": "Biologia"}

        resultado = repo.criar_pasta(usuario_id, "Biologia", None)

        assert resultado == {"id": pasta_id, "usuario_id": usuario_id, "nome": "Biologia"}
        mock_conn.commit.assert_called_once()

    def test_criar_pasta_quando_returning_vazio_levanta_document_database_error_e_faz_rollback(
        self, repo, mock_conn, mock_cursor
    ):
        mock_cursor.fetchone.return_value = None

        with pytest.raises(DocumentDatabaseError):
            repo.criar_pasta(uuid4(), "Biologia", None)

        mock_conn.rollback.assert_called_once()

    def test_criar_pasta_quando_banco_falha_levanta_document_database_error_preservando_causa(
        self, repo, mock_conn, mock_cursor
    ):
        causa = Exception("conexão perdida")
        mock_cursor.execute.side_effect = causa

        with pytest.raises(DocumentDatabaseError) as exc_info:
            repo.criar_pasta(uuid4(), "Biologia", None)

        assert exc_info.value.__cause__ is causa
        mock_conn.rollback.assert_called_once()


class TestCriarDocumento:
    def test_criar_documento_com_sucesso_retorna_dict(self, repo, mock_cursor, mock_conn):
        documento_id = uuid4()
        mock_cursor.fetchone.return_value = {"id": documento_id, "status": "processando"}

        resultado = repo.criar_documento(uuid4(), uuid4(), "Prova.pdf", ".pdf")

        assert resultado["id"] == documento_id
        mock_conn.commit.assert_called_once()

    def test_criar_documento_quando_returning_vazio_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        with pytest.raises(DocumentDatabaseError):
            repo.criar_documento(uuid4(), uuid4(), "Prova.pdf", ".pdf")

        mock_conn.rollback.assert_called_once()

    def test_criar_documento_quando_banco_falha_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.criar_documento(uuid4(), uuid4(), "Prova.pdf", ".pdf")


class TestAtualizarChaveS3:
    def test_atualizar_chave_s3_com_sucesso(self, repo, mock_cursor, mock_conn):
        documento_id = uuid4()
        mock_cursor.fetchone.return_value = {"id": documento_id, "chave_s3": "nova-chave"}

        resultado = repo.atualizar_chave_s3(documento_id, "nova-chave")

        assert resultado["chave_s3"] == "nova-chave"
        mock_conn.commit.assert_called_once()

    def test_atualizar_chave_s3_quando_documento_nao_existe_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        with pytest.raises(DocumentDatabaseError):
            repo.atualizar_chave_s3(uuid4(), "nova-chave")

        mock_conn.rollback.assert_called_once()

    def test_atualizar_chave_s3_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("timeout")

        with pytest.raises(DocumentDatabaseError):
            repo.atualizar_chave_s3(uuid4(), "nova-chave")


class TestBuscarChaveS3:
    def test_buscar_chave_s3_retorna_row_quando_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = {"chave_s3": "chave-x"}

        resultado = repo.buscar_chave_s3_por_documento_id_e_usuario(uuid4(), uuid4())

        assert resultado == {"chave_s3": "chave-x"}

    def test_buscar_chave_s3_retorna_none_quando_nao_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = None

        resultado = repo.buscar_chave_s3_por_documento_id_e_usuario(uuid4(), uuid4())

        assert resultado is None

    def test_buscar_chave_s3_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.buscar_chave_s3_por_documento_id_e_usuario(uuid4(), uuid4())


class TestListarPastasRaiz:
    def test_listar_pastas_raiz_retorna_lista(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = [{"id": uuid4(), "nome": "A"}]

        resultado = repo.listar_pastas_raiz_por_usuario(uuid4(), 50, 0)

        assert len(resultado) == 1

    def test_listar_pastas_raiz_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.listar_pastas_raiz_por_usuario(uuid4(), 50, 0)


class TestListarTodasPastas:
    def test_listar_todas_pastas_retorna_lista(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = [{"id": uuid4(), "nome": "A"}]

        resultado = repo.listar_todas_pastas_por_usuario(uuid4())

        assert len(resultado) == 1

    def test_listar_todas_pastas_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.listar_todas_pastas_por_usuario(uuid4())


class TestListarConteudoPasta:
    def test_listar_conteudo_pasta_retorna_none_quando_pasta_nao_pertence_ao_usuario(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = None

        resultado = repo.listar_conteudo_pasta(uuid4(), uuid4(), 50, 0)

        assert resultado is None

    def test_listar_conteudo_pasta_retorna_estrutura_com_paginacao(self, repo, mock_cursor):
        mock_cursor.fetchone.side_effect = [{"1": 1}, {"total": 7}]
        mock_cursor.fetchall.side_effect = [
            [{"id": uuid4(), "nome": "Sub"}],
            [{"id": uuid4(), "nome": "Doc", "status": "concluido", "resumo": None}],
        ]

        resultado = repo.listar_conteudo_pasta(uuid4(), uuid4(), 5, 0)

        assert resultado["total_arquivos"] == 7
        assert resultado["pagina_atual"] == 1
        assert resultado["tem_mais_paginas"] is True
        assert len(resultado["subpastas"]) == 1
        assert len(resultado["arquivos"]) == 1

    def test_listar_conteudo_pasta_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.listar_conteudo_pasta(uuid4(), uuid4(), 50, 0)


class TestAtualizarPastaNome:
    def test_atualizar_pasta_nome_com_sucesso(self, repo, mock_cursor, mock_conn):
        pasta_id = uuid4()
        mock_cursor.fetchone.return_value = {"id": pasta_id, "nome": "Novo nome"}

        resultado = repo.atualizar_pasta_nome(pasta_id, "Novo nome", uuid4())

        assert resultado["nome"] == "Novo nome"
        mock_conn.commit.assert_called_once()

    def test_atualizar_pasta_nome_retorna_none_quando_pasta_nao_encontrada(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        resultado = repo.atualizar_pasta_nome(uuid4(), "Novo nome", uuid4())

        assert resultado is None
        mock_conn.rollback.assert_called_once()

    def test_atualizar_pasta_nome_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.atualizar_pasta_nome(uuid4(), "Novo nome", uuid4())


class TestDeletarPasta:
    def test_deletar_pasta_retorna_true_quando_deletada(self, repo, mock_cursor, mock_conn):
        mock_cursor.rowcount = 1

        resultado = repo.deletar_pasta(uuid4(), uuid4())

        assert resultado is True
        mock_conn.commit.assert_called_once()

    def test_deletar_pasta_retorna_false_quando_nao_encontrada(self, repo, mock_cursor):
        mock_cursor.rowcount = 0

        resultado = repo.deletar_pasta(uuid4(), uuid4())

        assert resultado is False

    def test_deletar_pasta_quando_banco_falha_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.deletar_pasta(uuid4(), uuid4())

        mock_conn.rollback.assert_called_once()


class TestInserirDocumento:
    def test_inserir_documento_com_sucesso(self, repo, mock_cursor, mock_conn):
        documento_id = uuid4()
        mock_cursor.fetchone.return_value = {"id": documento_id, "nome": "Doc", "status": "concluido"}

        resultado = repo.inserir_documento(uuid4(), uuid4(), "Doc", "chave", "resumo texto")

        assert resultado["id"] == documento_id
        mock_conn.commit.assert_called_once()

    def test_inserir_documento_quando_returning_vazio_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        with pytest.raises(DocumentDatabaseError):
            repo.inserir_documento(uuid4(), uuid4(), "Doc", "chave", "resumo")

        mock_conn.rollback.assert_called_once()

    def test_inserir_documento_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.inserir_documento(uuid4(), uuid4(), "Doc", "chave", "resumo")


class TestAtualizarDocumentoNome:
    def test_atualizar_documento_nome_com_sucesso(self, repo, mock_cursor, mock_conn):
        documento_id = uuid4()
        mock_cursor.fetchone.return_value = {"id": documento_id, "nome": "Renomeado"}

        resultado = repo.atualizar_documento_nome(documento_id, "Renomeado", uuid4())

        assert resultado["nome"] == "Renomeado"
        mock_conn.commit.assert_called_once()

    def test_atualizar_documento_nome_retorna_none_quando_nao_encontrado(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None

        resultado = repo.atualizar_documento_nome(uuid4(), "Renomeado", uuid4())

        assert resultado is None
        mock_conn.rollback.assert_called_once()

    def test_atualizar_documento_nome_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.atualizar_documento_nome(uuid4(), "Renomeado", uuid4())


class TestDeletarDocumento:
    def test_deletar_documento_retorna_true_quando_deletado(self, repo, mock_cursor, mock_conn):
        mock_cursor.rowcount = 1

        resultado = repo.deletar_documento(uuid4(), uuid4())

        assert resultado is True
        mock_conn.commit.assert_called_once()

    def test_deletar_documento_retorna_false_quando_nao_encontrado(self, repo, mock_cursor):
        mock_cursor.rowcount = 0

        resultado = repo.deletar_documento(uuid4(), uuid4())

        assert resultado is False

    def test_deletar_documento_quando_banco_falha_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.deletar_documento(uuid4(), uuid4())

        mock_conn.rollback.assert_called_once()


class TestMontarPadraoBusca:
    def test_remove_acentos_e_caixa(self):
        from app.repositories.DocumentRepository import montar_padrao_busca

        assert montar_padrao_busca("  ANSIEDADE Emoção ") == "%ansiedade emocao%"

    def test_neutraliza_caracteres_especiais_do_like(self):
        from app.repositories.DocumentRepository import montar_padrao_busca

        assert montar_padrao_busca("100%_ok!") == "%100!%!_ok!!%"

    def test_termo_vazio_casa_com_tudo(self):
        from app.repositories.DocumentRepository import montar_padrao_busca

        assert montar_padrao_busca("") == "%%"


class TestBuscarDocumentos:
    def test_retorna_itens_e_total(self, repo, mock_cursor):
        itens = [{"id": uuid4(), "nome": "Sono", "pasta_nome": "Saúde", "criado_em": "2026-01-01"}]
        mock_cursor.fetchall.return_value = itens
        mock_cursor.fetchone.return_value = {"total": 7}

        resultado = repo.buscar_documentos(uuid4(), "sono", 20, 0)

        assert resultado == {"itens": itens, "total": 7}

    def test_envia_usuario_padrao_normalizado_e_paginacao_para_o_banco(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = {"total": 0}
        usuario_id = uuid4()

        repo.buscar_documentos(usuario_id, "Emoção", 10, 30)

        primeira, segunda = mock_cursor.execute.call_args_list
        assert primeira.args[1] == (usuario_id, usuario_id, "%emocao%", 10, 30)
        assert segunda.args[1] == (usuario_id, "%emocao%")
        assert "d.usuario_id = %s" in primeira.args[0]

    def test_consulta_monta_o_caminho_das_pastas_com_cte_recursiva_limitada(self, repo, mock_cursor):
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = {"total": 0}

        repo.buscar_documentos(uuid4(), "", 20, 0)

        consulta = mock_cursor.execute.call_args_list[0].args[0]
        assert "WITH RECURSIVE arvore" in consulta
        assert "pasta_caminho" in consulta
        assert "a.nivel < 20" in consulta

    def test_quando_banco_falha_levanta_document_database_error(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(DocumentDatabaseError):
            repo.buscar_documentos(uuid4(), "x", 20, 0)
