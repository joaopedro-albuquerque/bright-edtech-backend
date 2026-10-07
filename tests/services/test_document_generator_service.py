from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import DocumentNotFoundError, ValidationNotificationError
from app.services.DocumentGeneratorService import DocumentGeneratorService


@pytest.fixture
def document_repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def s3_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def service(document_repo, s3_service):
    return DocumentGeneratorService(document_repo, s3_service)


def _upload_file(filename="prova.pdf", content_type="application/pdf", size=1024):
    return SimpleNamespace(filename=filename, content_type=content_type, size=size, file=b"conteudo")


class TestValidarArquivoPdf:
    def test_arquivo_pdf_valido_nao_levanta_erro(self, service):
        service._validar_arquivo_pdf(_upload_file(), ".pdf")

    def test_extensao_diferente_de_pdf_levanta_validation_notification_error(self, service):
        arquivo = _upload_file(filename="prova.docx", content_type="application/pdf")

        with pytest.raises(ValidationNotificationError) as exc_info:
            service._validar_arquivo_pdf(arquivo, ".docx")

        assert exc_info.value.notifications[0].code == 1003

    def test_content_type_diferente_de_pdf_levanta_validation_notification_error(self, service):
        arquivo = _upload_file(content_type="application/octet-stream")

        with pytest.raises(ValidationNotificationError) as exc_info:
            service._validar_arquivo_pdf(arquivo, ".pdf")

        assert exc_info.value.notifications[0].code == 1003

    def test_arquivo_acima_de_5mb_levanta_validation_notification_error(self, service):
        arquivo = _upload_file(size=6 * 1024 * 1024)

        with pytest.raises(ValidationNotificationError) as exc_info:
            service._validar_arquivo_pdf(arquivo, ".pdf")

        assert exc_info.value.notifications[0].code == 1004

    def test_formato_invalido_e_tamanho_excedido_retornam_as_duas_notificacoes(self, service):
        arquivo = _upload_file(filename="prova.exe", content_type="application/exe", size=6 * 1024 * 1024)

        with pytest.raises(ValidationNotificationError) as exc_info:
            service._validar_arquivo_pdf(arquivo, ".exe")

        codigos = {n.code for n in exc_info.value.notifications}
        assert codigos == {1003, 1004}

    def test_size_none_nao_levanta_erro_de_tamanho(self, service):
        arquivo = _upload_file(size=None)

        service._validar_arquivo_pdf(arquivo, ".pdf")


class TestCriarPastaService:
    def test_criar_pasta_com_sucesso_delega_para_repositorio(self, service, document_repo):
        document_repo.criar_pasta.return_value = {"id": uuid4(), "nome": "Biologia"}

        resultado = service.criar_pasta_service(uuid4(), "Biologia", None)

        assert resultado["nome"] == "Biologia"
        document_repo.criar_pasta.assert_called_once()


class TestSalvarDocumento:
    def test_salvar_documento_com_sucesso_cria_registra_e_atualiza_chave_s3(
        self, service, document_repo, s3_service
    ):
        documento_id = uuid4()
        document_repo.criar_documento.return_value = {"id": documento_id}
        s3_service.build_document_key.return_value = "usuarios/u/documentos/d.pdf"
        s3_service.bucket_name = "bucket-teste"
        document_repo.atualizar_chave_s3.return_value = {
            "id": documento_id, "status": "concluido", "resumo": None, "chave_s3": "usuarios/u/documentos/d.pdf",
        }

        resultado = service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        assert resultado["id"] == documento_id
        assert resultado["s3_url"] == "s3://bucket-teste/usuarios/u/documentos/d.pdf"
        s3_service.upload_file.assert_called_once()

    def test_salvar_documento_com_arquivo_invalido_nao_chama_repositorio(self, service, document_repo):
        with pytest.raises(ValidationNotificationError):
            service.salvar_documento(_upload_file(filename="prova.txt"), uuid4(), uuid4(), "Prova")

        document_repo.criar_documento.assert_not_called()


class TestGerarPreSignedUrlVisualizacao:
    def test_com_sucesso_retorna_url(self, service, document_repo, s3_service):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": "chave.pdf"}
        s3_service.generate_presigned_url.return_value = "https://s3/url"

        resultado = service.gerar_pre_signed_url_visualizacao(uuid4(), uuid4())

        assert resultado == "https://s3/url"

    def test_quando_documento_nao_encontrado_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = None

        with pytest.raises(DocumentNotFoundError):
            service.gerar_pre_signed_url_visualizacao(uuid4(), uuid4())

    def test_quando_documento_sem_chave_s3_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": None}

        with pytest.raises(DocumentNotFoundError):
            service.gerar_pre_signed_url_visualizacao(uuid4(), uuid4())


class TestListagens:
    def test_listar_pastas_raiz_por_usuario_delega_para_repositorio(self, service, document_repo):
        document_repo.listar_pastas_raiz_por_usuario.return_value = [{"id": uuid4()}]

        resultado = service.listar_pastas_raiz_por_usuario(uuid4(), 50, 0)

        assert len(resultado) == 1

    def test_listar_todas_pastas_por_usuario_delega_para_repositorio(self, service, document_repo):
        document_repo.listar_todas_pastas_por_usuario.return_value = [{"id": uuid4()}]

        resultado = service.listar_todas_pastas_por_usuario(uuid4())

        assert len(resultado) == 1

    def test_listar_conteudo_pasta_com_sucesso(self, service, document_repo):
        document_repo.listar_conteudo_pasta.return_value = {"total_arquivos": 0}

        resultado = service.listar_conteudo_pasta(uuid4(), uuid4(), 50, 0)

        assert resultado == {"total_arquivos": 0}

    def test_listar_conteudo_pasta_quando_nao_encontrada_levanta_erro(self, service, document_repo):
        document_repo.listar_conteudo_pasta.return_value = None

        with pytest.raises(DocumentNotFoundError):
            service.listar_conteudo_pasta(uuid4(), uuid4(), 50, 0)


class TestAtualizarPastaNome:
    def test_com_sucesso_retorna_pasta_atualizada(self, service, document_repo):
        document_repo.atualizar_pasta_nome.return_value = {"nome": "Novo nome"}

        resultado = service.atualizar_pasta_nome(uuid4(), "Novo nome", uuid4())

        assert resultado["nome"] == "Novo nome"

    def test_quando_nao_encontrada_levanta_document_not_found_error(self, service, document_repo):
        document_repo.atualizar_pasta_nome.return_value = None

        with pytest.raises(DocumentNotFoundError):
            service.atualizar_pasta_nome(uuid4(), "Novo nome", uuid4())


class TestAtualizarDocumentoNome:
    def test_com_sucesso_retorna_documento_atualizado(self, service, document_repo):
        document_repo.atualizar_documento_nome.return_value = {"nome": "Renomeado"}

        resultado = service.atualizar_documento_nome(uuid4(), "Renomeado", uuid4())

        assert resultado["nome"] == "Renomeado"

    def test_quando_nao_encontrado_levanta_document_not_found_error(self, service, document_repo):
        document_repo.atualizar_documento_nome.return_value = None

        with pytest.raises(DocumentNotFoundError):
            service.atualizar_documento_nome(uuid4(), "Renomeado", uuid4())


class TestDeletarDocumento:
    def test_com_sucesso_nao_levanta_erro(self, service, document_repo):
        document_repo.deletar_documento.return_value = True

        service.deletar_documento(uuid4(), uuid4())

    def test_quando_nao_encontrado_levanta_document_not_found_error(self, service, document_repo):
        document_repo.deletar_documento.return_value = False

        with pytest.raises(DocumentNotFoundError):
            service.deletar_documento(uuid4(), uuid4())


class TestDeletarPasta:
    def test_com_sucesso_nao_levanta_erro(self, service, document_repo):
        document_repo.deletar_pasta.return_value = True

        service.deletar_pasta(uuid4(), uuid4())

    def test_quando_nao_encontrada_levanta_document_not_found_error(self, service, document_repo):
        document_repo.deletar_pasta.return_value = False

        with pytest.raises(DocumentNotFoundError):
            service.deletar_pasta(uuid4(), uuid4())
