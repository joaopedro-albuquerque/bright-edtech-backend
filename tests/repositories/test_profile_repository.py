from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import ProfileDatabaseError
from app.repositories.ProfileRepository import ProfileRepository
from app.schemas.user_schema import OnboardingRequest, UsuarioBase


@pytest.fixture
def repo(mock_conn):
    return ProfileRepository(mock_conn)


def _usuario_row(**overrides):
    row = {
        "id": uuid4(),
        "email": "aluno@exemplo.com",
        "nome": "Aluno Teste",
        "estilo_preferido": None,
        "formato_preferido": None,
        "objetivos_estudo": None,
        "cognito_id": "cognito-123",
        "termos_versao": "1.0",
        "tour_concluido": False,
        "termos_aceitos_em": datetime.utcnow(),
        "criado_em": datetime.utcnow(),
        "atualizado_em": datetime.utcnow(),
    }
    row.update(overrides)
    return row


class TestCriarUsuario:
    def test_criar_usuario_com_sucesso_retorna_usuario_e_commita(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = _usuario_row()
        usuario = UsuarioBase(email="aluno@exemplo.com", termos_versao="1.0")

        resultado = repo.criar_usuario(usuario)

        assert resultado.email == "aluno@exemplo.com"
        mock_conn.commit.assert_called_once()

    def test_criar_usuario_quando_returning_vazio_levanta_erro_e_faz_rollback(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None
        usuario = UsuarioBase(email="aluno@exemplo.com")

        with pytest.raises(ProfileDatabaseError):
            repo.criar_usuario(usuario)

        mock_conn.rollback.assert_called_once()

    def test_criar_usuario_quando_banco_falha_levanta_erro_preservando_causa(self, repo, mock_cursor):
        causa = Exception("email duplicado")
        mock_cursor.execute.side_effect = causa
        usuario = UsuarioBase(email="aluno@exemplo.com")

        with pytest.raises(ProfileDatabaseError) as exc_info:
            repo.criar_usuario(usuario)

        assert exc_info.value.__cause__ is causa


class TestAtualizarUsuarioPorId:
    def test_atualizar_usuario_com_sucesso(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = _usuario_row(nome="Novo Nome")
        usuario = UsuarioBase(email="aluno@exemplo.com", nome="Novo Nome")

        resultado = repo.atualizar_usuario_por_id(uuid4(), usuario)

        assert resultado.nome == "Novo Nome"
        mock_conn.commit.assert_called_once()

    def test_atualizar_usuario_retorna_none_quando_nao_encontrado(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None
        usuario = UsuarioBase(email="aluno@exemplo.com")

        resultado = repo.atualizar_usuario_por_id(uuid4(), usuario)

        assert resultado is None
        mock_conn.rollback.assert_called_once()

    def test_atualizar_usuario_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")
        usuario = UsuarioBase(email="aluno@exemplo.com")

        with pytest.raises(ProfileDatabaseError):
            repo.atualizar_usuario_por_id(uuid4(), usuario)


class TestAtualizarPerfilOnboarding:
    def test_atualizar_perfil_onboarding_com_sucesso(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = _usuario_row()
        perfil = OnboardingRequest(objetivos_estudo="Passar no ENEM")

        resultado = repo.atualizar_perfil_onboarding(uuid4(), perfil)

        assert resultado.email == "aluno@exemplo.com"
        mock_conn.commit.assert_called_once()

    def test_atualizar_perfil_onboarding_retorna_none_quando_nao_encontrado(self, repo, mock_cursor, mock_conn):
        mock_cursor.fetchone.return_value = None
        perfil = OnboardingRequest()

        resultado = repo.atualizar_perfil_onboarding(uuid4(), perfil)

        assert resultado is None
        mock_conn.rollback.assert_called_once()

    def test_atualizar_perfil_onboarding_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")
        perfil = OnboardingRequest()

        with pytest.raises(ProfileDatabaseError):
            repo.atualizar_perfil_onboarding(uuid4(), perfil)


class TestBuscarUsuarioPorId:
    def test_buscar_usuario_por_id_retorna_usuario_quando_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = _usuario_row()

        resultado = repo.buscar_usuario_por_id(uuid4())

        assert resultado.email == "aluno@exemplo.com"

    def test_buscar_usuario_por_id_retorna_none_quando_nao_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = None

        resultado = repo.buscar_usuario_por_id(uuid4())

        assert resultado is None

    def test_buscar_usuario_por_id_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(ProfileDatabaseError):
            repo.buscar_usuario_por_id(uuid4())


class TestDeletarUsuarioPorId:
    def test_deletar_usuario_retorna_true_quando_deletado(self, repo, mock_cursor, mock_conn):
        mock_cursor.rowcount = 1

        resultado = repo.deletar_usuario_por_id(uuid4())

        assert resultado is True
        mock_conn.commit.assert_called_once()

    def test_deletar_usuario_retorna_false_quando_nao_encontrado(self, repo, mock_cursor):
        mock_cursor.rowcount = 0

        resultado = repo.deletar_usuario_por_id(uuid4())

        assert resultado is False

    def test_deletar_usuario_quando_banco_falha_levanta_erro(self, repo, mock_cursor, mock_conn):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(ProfileDatabaseError):
            repo.deletar_usuario_por_id(uuid4())

        mock_conn.rollback.assert_called_once()


class TestBuscarUsuarioPorCognitoId:
    def test_buscar_por_cognito_id_retorna_usuario_quando_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = _usuario_row(cognito_id="cognito-abc")

        resultado = repo.buscar_usuario_por_cognito_id("cognito-abc")

        assert resultado.cognito_id == "cognito-abc"

    def test_buscar_por_cognito_id_retorna_none_quando_nao_encontrado(self, repo, mock_cursor):
        mock_cursor.fetchone.return_value = None

        resultado = repo.buscar_usuario_por_cognito_id("cognito-inexistente")

        assert resultado is None

    def test_buscar_por_cognito_id_quando_banco_falha_levanta_erro(self, repo, mock_cursor):
        mock_cursor.execute.side_effect = Exception("falha")

        with pytest.raises(ProfileDatabaseError):
            repo.buscar_usuario_por_cognito_id("cognito-abc")
