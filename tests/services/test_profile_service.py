from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.config import TERMOS_DE_USO_VERSAO
from app.core.exceptions import ProfileNotFoundError, ValidationNotificationError
from app.schemas.user_schema import OnboardingRequest, UsuarioBase
from app.services.ProfileService import ProfileService


@pytest.fixture
def repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def service(repo):
    return ProfileService(repo)


class TestCriarUsuario:
    def test_com_dados_validos_cria_usuario_e_retorna(self, service, repo):
        usuario_criado = SimpleNamespace(id=uuid4())
        repo.criar_usuario.return_value = usuario_criado
        usuario = UsuarioBase(email="a@a.com", termos_versao=TERMOS_DE_USO_VERSAO)

        resultado = service.criar_usuario(usuario)

        assert resultado is usuario_criado
        repo.criar_usuario.assert_called_once_with(usuario)

    def test_estilo_preferido_invalido_levanta_validation_notification_error(self, service, repo):
        usuario = UsuarioBase(email="a@a.com", termos_versao=TERMOS_DE_USO_VERSAO, estilo_preferido="inexistente")

        with pytest.raises(ValidationNotificationError) as exc_info:
            service.criar_usuario(usuario)

        assert exc_info.value.notifications[0].code == 2101
        repo.criar_usuario.assert_not_called()

    def test_formato_preferido_invalido_levanta_validation_notification_error(self, service, repo):
        usuario = UsuarioBase(email="a@a.com", termos_versao=TERMOS_DE_USO_VERSAO, formato_preferido="inexistente")

        with pytest.raises(ValidationNotificationError) as exc_info:
            service.criar_usuario(usuario)

        assert exc_info.value.notifications[0].code == 2102

    def test_termos_versao_desatualizada_levanta_validation_notification_error(self, service, repo):
        usuario = UsuarioBase(email="a@a.com", termos_versao="0.1")

        with pytest.raises(ValidationNotificationError) as exc_info:
            service.criar_usuario(usuario)

        assert exc_info.value.notifications[0].code == 2103

    def test_multiplos_campos_invalidos_retornam_todas_as_notificacoes_juntas(self, service, repo):
        usuario = UsuarioBase(
            email="a@a.com", termos_versao="0.1", estilo_preferido="x", formato_preferido="y",
        )

        with pytest.raises(ValidationNotificationError) as exc_info:
            service.criar_usuario(usuario)

        codigos = {n.code for n in exc_info.value.notifications}
        assert codigos == {2101, 2102, 2103}


class TestBuscarUsuarioPorId:
    def test_com_sucesso_retorna_usuario(self, service, repo):
        repo.buscar_usuario_por_id.return_value = "usuario"

        resultado = service.buscar_usuario_por_id(uuid4())

        assert resultado == "usuario"

    def test_quando_nao_encontrado_levanta_profile_not_found_error(self, service, repo):
        repo.buscar_usuario_por_id.return_value = None

        with pytest.raises(ProfileNotFoundError):
            service.buscar_usuario_por_id(uuid4())


class TestAtualizarUsuarioPorId:
    def test_com_sucesso_retorna_usuario_atualizado(self, service, repo):
        repo.atualizar_usuario_por_id.return_value = "usuario-atualizado"
        usuario = UsuarioBase(email="a@a.com")

        resultado = service.atualizar_usuario_por_id(uuid4(), usuario)

        assert resultado == "usuario-atualizado"

    def test_nao_exige_termos_versao_na_atualizacao(self, service, repo):
        repo.atualizar_usuario_por_id.return_value = "usuario-atualizado"
        usuario = UsuarioBase(email="a@a.com", termos_versao="versao-antiga-qualquer")

        resultado = service.atualizar_usuario_por_id(uuid4(), usuario)

        assert resultado == "usuario-atualizado"

    def test_quando_nao_encontrado_levanta_profile_not_found_error(self, service, repo):
        repo.atualizar_usuario_por_id.return_value = None
        usuario = UsuarioBase(email="a@a.com")

        with pytest.raises(ProfileNotFoundError):
            service.atualizar_usuario_por_id(uuid4(), usuario)

    def test_estilo_preferido_invalido_levanta_validation_notification_error(self, service, repo):
        usuario = UsuarioBase(email="a@a.com", estilo_preferido="inexistente")

        with pytest.raises(ValidationNotificationError):
            service.atualizar_usuario_por_id(uuid4(), usuario)


class TestAtualizarPerfilOnboarding:
    def test_com_sucesso_retorna_usuario_atualizado(self, service, repo):
        repo.atualizar_perfil_onboarding.return_value = "usuario-atualizado"

        resultado = service.atualizar_perfil_onboarding(uuid4(), OnboardingRequest())

        assert resultado == "usuario-atualizado"

    def test_quando_nao_encontrado_levanta_profile_not_found_error(self, service, repo):
        repo.atualizar_perfil_onboarding.return_value = None

        with pytest.raises(ProfileNotFoundError):
            service.atualizar_perfil_onboarding(uuid4(), OnboardingRequest())


class TestDeletarUsuarioPorId:
    def test_com_sucesso_nao_levanta_erro(self, service, repo):
        repo.deletar_usuario_por_id.return_value = True

        service.deletar_usuario_por_id(uuid4())

    def test_quando_nao_encontrado_levanta_profile_not_found_error(self, service, repo):
        repo.deletar_usuario_por_id.return_value = False

        with pytest.raises(ProfileNotFoundError):
            service.deletar_usuario_por_id(uuid4())


class TestBuscarUsuarioPorCognitoId:
    def test_com_sucesso_retorna_usuario(self, service, repo):
        repo.buscar_usuario_por_cognito_id.return_value = "usuario"

        resultado = service.buscar_usuario_por_cognito_id("cognito-123")

        assert resultado == "usuario"

    def test_quando_nao_encontrado_levanta_profile_not_found_error(self, service, repo):
        repo.buscar_usuario_por_cognito_id.return_value = None

        with pytest.raises(ProfileNotFoundError):
            service.buscar_usuario_por_cognito_id("cognito-123")
