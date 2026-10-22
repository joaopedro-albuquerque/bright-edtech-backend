import io
import json

import pytest
from botocore.exceptions import ClientError

from app.core.exceptions import StorageError
from app.services.S3Service import S3Service


def _client_error(op="Operacao"):
    return ClientError({"Error": {"Code": "AccessDenied", "Message": "negado"}}, op)


@pytest.fixture
def mock_boto_client(mocker):
    return mocker.patch("app.services.S3Service.boto3.client")


@pytest.fixture
def service(mock_boto_client):
    return S3Service(bucket_name="bucket-teste")


class TestInit:
    def test_init_usa_bucket_name_informado(self, mock_boto_client):
        service = S3Service(bucket_name="meu-bucket")

        assert service.bucket_name == "meu-bucket"

    def test_init_usa_env_var_quando_bucket_name_nao_informado(self, mock_boto_client, monkeypatch):
        monkeypatch.setenv("S3_BUCKET_NAME", "bucket-do-env")

        service = S3Service()

        assert service.bucket_name == "bucket-do-env"

    def test_init_levanta_value_error_quando_bucket_nao_configurado(self, mock_boto_client, monkeypatch):
        monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

        with pytest.raises(ValueError, match="S3_BUCKET_NAME"):
            S3Service()


def test_build_document_key_monta_caminho_esperado(service):
    resultado = service.build_document_key("user-1", "doc-1", ".pdf")

    assert resultado == "usuarios/user-1/doc-1/original.pdf"


class TestUploadFile:
    def test_upload_file_com_sucesso_retorna_metadados(self, service):
        resultado = service.upload_file(io.BytesIO(b"conteudo"), "chave.pdf")

        assert resultado == {
            "bucket": "bucket-teste",
            "key": "chave.pdf",
            "s3_url": "s3://bucket-teste/chave.pdf",
        }

    def test_upload_file_quando_s3_falha_levanta_storage_error(self, service):
        service.client.upload_fileobj.side_effect = _client_error()

        with pytest.raises(StorageError):
            service.upload_file(io.BytesIO(b"x"), "chave.pdf")


class TestGeneratePresignedUrl:
    def test_generate_presigned_url_com_sucesso(self, service):
        service.client.generate_presigned_url.return_value = "https://s3/presigned"

        resultado = service.generate_presigned_url("chave.pdf")

        assert resultado == "https://s3/presigned"

    def test_generate_presigned_url_quando_s3_falha_levanta_storage_error(self, service):
        service.client.generate_presigned_url.side_effect = _client_error()

        with pytest.raises(StorageError):
            service.generate_presigned_url("chave.pdf")


class TestDownloadFile:
    def test_download_file_com_sucesso_retorna_bytesio(self, service):
        service.client.get_object.return_value = {"Body": io.BytesIO(b"conteudo-pdf")}

        resultado = service.download_file("chave.pdf")

        assert resultado.read() == b"conteudo-pdf"

    def test_download_file_quando_s3_falha_levanta_storage_error(self, service):
        service.client.get_object.side_effect = _client_error()

        with pytest.raises(StorageError):
            service.download_file("chave.pdf")


class TestUploadText:
    def test_upload_text_com_sucesso(self, service):
        resultado = service.upload_text("# titulo", "chave.md")

        assert resultado["key"] == "chave.md"
        service.client.put_object.assert_called_once()

    def test_upload_text_quando_s3_falha_levanta_storage_error(self, service):
        service.client.put_object.side_effect = _client_error()

        with pytest.raises(StorageError):
            service.upload_text("texto", "chave.md")


class TestUploadBytes:
    def test_upload_bytes_com_sucesso(self, service):
        resultado = service.upload_bytes(b"binario", "chave.pdf", content_type="application/pdf")

        assert resultado["key"] == "chave.pdf"

    def test_upload_bytes_quando_s3_falha_levanta_storage_error(self, service):
        service.client.put_object.side_effect = _client_error()

        with pytest.raises(StorageError):
            service.upload_bytes(b"x", "chave.pdf", content_type="application/pdf")


def test_upload_json_serializa_e_delega_para_upload_text(service, mocker):
    upload_text_spy = mocker.patch.object(service, "upload_text", return_value={"key": "chave.json"})

    service.upload_json({"a": 1}, "chave.json")

    upload_text_spy.assert_called_once_with(
        json.dumps({"a": 1}, ensure_ascii=False, indent=2), "chave.json", content_type="application/json"
    )


class TestDownloadJson:
    def test_download_json_com_sucesso_retorna_objeto_decodificado(self, service):
        service.client.get_object.return_value = {"Body": io.BytesIO(json.dumps({"a": 1}).encode())}

        resultado = service.download_json("chave.json")

        assert resultado == {"a": 1}

    def test_download_json_quando_s3_falha_levanta_storage_error(self, service):
        service.client.get_object.side_effect = _client_error()

        with pytest.raises(StorageError):
            service.download_json("chave.json")


class TestDownloadText:
    def test_download_text_com_sucesso(self, service):
        service.client.get_object.return_value = {"Body": io.BytesIO("conteúdo".encode("utf-8"))}

        resultado = service.download_text("chave.md")

        assert resultado == "conteúdo"

    def test_download_text_quando_s3_falha_levanta_storage_error(self, service):
        service.client.get_object.side_effect = _client_error()

        with pytest.raises(StorageError):
            service.download_text("chave.md")


class TestDeletePrefix:
    def test_prefixos_e_chaves_ficam_sob_o_mesmo_usuario(self, service):
        assert service.build_user_prefix("u1") == "usuarios/u1/"
        assert service.build_document_prefix("u1", "d1") == "usuarios/u1/d1/"
        assert service.build_artifact_key("u1", "d1", "quiz-5.json") == "usuarios/u1/d1/quiz-5.json"

    def test_apaga_todos_os_objetos_paginados(self, service):
        service.client.get_paginator.return_value.paginate.return_value = [
            {"Contents": [{"Key": "usuarios/u1/a.pdf"}, {"Key": "usuarios/u1/b.pdf"}]},
            {},
            {"Contents": [{"Key": "usuarios/u1/c.pdf"}]},
        ]

        removidos = service.delete_prefix("usuarios/u1/")

        assert removidos == 3
        assert service.client.delete_objects.call_count == 2
        service.client.get_paginator.return_value.paginate.assert_called_once_with(
            Bucket="bucket-teste", Prefix="usuarios/u1/"
        )

    def test_sem_objetos_retorna_zero(self, service):
        service.client.get_paginator.return_value.paginate.return_value = [{}]

        assert service.delete_prefix("usuarios/u1/") == 0
        service.client.delete_objects.assert_not_called()

    def test_erro_do_s3_vira_storage_error(self, service):
        service.client.get_paginator.return_value.paginate.side_effect = _client_error()

        with pytest.raises(StorageError):
            service.delete_prefix("usuarios/u1/")
