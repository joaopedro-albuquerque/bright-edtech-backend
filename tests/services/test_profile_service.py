from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.config import TERMOS_DE_USO_VERSAO
from app.core.exceptions import ProfileNotFoundError, StorageError, ValidationNotificationError
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
    @pytest.fixture
    def s3(self, mocker):
        s3 = mocker.MagicMock()
        s3.build_user_prefix.side_effect = lambda uid: f"usuarios/{uid}/"
        s3.delete_prefix.return_value = 2
        return s3

    def test_apaga_arquivos_do_s3_e_depois_o_banco(self, repo, s3):
        service = ProfileService(repo, s3)
        user_id = uuid4()
        repo.buscar_usuario_por_id.return_value = "usuario"
        repo.deletar_usuario_por_id.return_value = True

        service.deletar_usuario_por_id(user_id)

        s3.delete_prefix.assert_called_once_with(f"usuarios/{user_id}/")
        repo.deletar_usuario_por_id.assert_called_once_with(user_id)

    def test_usuario_inexistente_levanta_not_found_sem_tocar_no_s3(self, repo, s3):
        service = ProfileService(repo, s3)
        repo.buscar_usuario_por_id.return_value = None

        with pytest.raises(ProfileNotFoundError):
            service.deletar_usuario_por_id(uuid4())

        s3.delete_prefix.assert_not_called()
        repo.deletar_usuario_por_id.assert_not_called()

    def test_falha_no_s3_nao_apaga_o_banco(self, repo, s3):
        service = ProfileService(repo, s3)
        repo.buscar_usuario_por_id.return_value = "usuario"
        s3.delete_prefix.side_effect = StorageError("falha")

        with pytest.raises(StorageError):
            service.deletar_usuario_por_id(uuid4())

        repo.deletar_usuario_por_id.assert_not_called()

    def test_removido_por_outra_requisicao_levanta_not_found(self, repo, s3):
        service = ProfileService(repo, s3)
        repo.buscar_usuario_por_id.return_value = "usuario"
        repo.deletar_usuario_por_id.return_value = False

        with pytest.raises(ProfileNotFoundError):
            service.deletar_usuario_por_id(uuid4())

    def test_s3_service_e_criado_sob_demanda(self, repo, mocker):
        criado = mocker.patch("app.services.ProfileService.S3Service")
        service = ProfileService(repo)

        assert service.s3_service is criado.return_value
        assert service.s3_service is criado.return_value
        criado.assert_called_once_with()


class TestBuscarUsuarioPorCognitoId:
    def test_com_sucesso_retorna_usuario(self, service, repo):
        repo.buscar_usuario_por_cognito_id.return_value = "usuario"

        resultado = service.buscar_usuario_por_cognito_id("cognito-123")

        assert resultado == "usuario"

    def test_quando_nao_encontrado_levanta_profile_not_found_error(self, service, repo):
        repo.buscar_usuario_por_cognito_id.return_value = None

        with pytest.raises(ProfileNotFoundError):
            service.buscar_usuario_por_cognito_id("cognito-123")
