from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import (
    AiGenerationError,
    ConteudoImproprioError,
    DocumentNotFoundError,
    ModeracaoIndisponivelError,
    StorageError,
    ValidationNotificationError,
)
from app.services.DocumentGeneratorService import DocumentGeneratorService


@pytest.fixture
def document_repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def s3_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def bedrock_service(mocker):
    bedrock = mocker.MagicMock()
    bedrock.moderar_conteudo.return_value = (False, "")
    return bedrock


@pytest.fixture(autouse=True)
def pdf_utils(mocker):
    contar = mocker.patch("app.services.DocumentGeneratorService.contar_paginas", return_value=3)
    amostrar = mocker.patch(
        "app.services.DocumentGeneratorService.amostrar_paginas", return_value=b"pdf-amostra"
    )
    return SimpleNamespace(contar=contar, amostrar=amostrar)


@pytest.fixture
def service(document_repo, s3_service, bedrock_service):
    return DocumentGeneratorService(document_repo, s3_service, bedrock_service)


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


class TestModeracaoDeConteudo:
    def _assert_nada_foi_salvo(self, document_repo, s3_service):
        document_repo.criar_documento.assert_not_called()
        s3_service.upload_file.assert_not_called()

    def test_conteudo_improprio_levanta_erro_e_nao_salva_nada(
        self, service, bedrock_service, document_repo, s3_service
    ):
        bedrock_service.moderar_conteudo.return_value = (True, "conteúdo sexual explícito")

        with pytest.raises(ConteudoImproprioError) as exc_info:
            service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        assert exc_info.value.code == 1005
        assert exc_info.value.http_status == 422
        self._assert_nada_foi_salvo(document_repo, s3_service)

    def test_falha_da_ia_bloqueia_upload_com_mensagem_clara(
        self, service, bedrock_service, document_repo, s3_service
    ):
        bedrock_service.moderar_conteudo.side_effect = AiGenerationError("bedrock e gemini fora")

        with pytest.raises(ModeracaoIndisponivelError) as exc_info:
            service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        assert exc_info.value.code == 9004
        assert exc_info.value.http_status == 503
        assert "problemas internos" in exc_info.value.message
        self._assert_nada_foi_salvo(document_repo, s3_service)

    def test_pdf_ilegivel_levanta_validation_notification_error(
        self, service, pdf_utils, bedrock_service, document_repo, s3_service
    ):
        pdf_utils.contar.side_effect = ValueError("O arquivo PDF está corrompido ou é ilegível.")

        with pytest.raises(ValidationNotificationError) as exc_info:
            service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        assert exc_info.value.notifications[0].code == 1006
        bedrock_service.moderar_conteudo.assert_not_called()
        self._assert_nada_foi_salvo(document_repo, s3_service)

    def test_pdf_sem_paginas_e_tratado_como_ilegivel(
        self, service, pdf_utils, bedrock_service, document_repo, s3_service
    ):
        pdf_utils.contar.return_value = 0

        with pytest.raises(ValidationNotificationError) as exc_info:
            service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        assert exc_info.value.notifications[0].code == 1006
        bedrock_service.moderar_conteudo.assert_not_called()

    def test_falha_ao_amostrar_paginas_levanta_erro_de_pdf_ilegivel(
        self, service, pdf_utils, bedrock_service, document_repo, s3_service
    ):
        pdf_utils.amostrar.side_effect = ValueError("O arquivo PDF está corrompido ou é ilegível.")

        with pytest.raises(ValidationNotificationError) as exc_info:
            service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        assert exc_info.value.notifications[0].code == 1006
        bedrock_service.moderar_conteudo.assert_not_called()
        self._assert_nada_foi_salvo(document_repo, s3_service)

    def test_pdf_acima_do_limite_de_paginas_e_recusado_sem_chamar_ia_nem_salvar(
        self, service, pdf_utils, bedrock_service, document_repo, s3_service
    ):
        pdf_utils.contar.return_value = 101

        with pytest.raises(ValidationNotificationError) as exc_info:
            service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        assert exc_info.value.notifications[0].code == 1008
        bedrock_service.moderar_conteudo.assert_not_called()
        self._assert_nada_foi_salvo(document_repo, s3_service)

    def test_pdf_com_exatamente_o_limite_de_paginas_e_aceito(self, service, pdf_utils, document_repo, s3_service):
        pdf_utils.contar.return_value = 100
        document_repo.criar_documento.return_value = {"id": uuid4()}
        document_repo.atualizar_chave_s3.return_value = {"id": uuid4()}

        service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        document_repo.criar_documento.assert_called_once()

    def test_pdf_escaneado_sem_camada_de_texto_e_moderado_e_aceito(
        self, service, bedrock_service, document_repo
    ):
        document_repo.criar_documento.return_value = {"id": uuid4()}
        document_repo.atualizar_chave_s3.return_value = {"id": uuid4()}

        service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        bedrock_service.moderar_conteudo.assert_called_once()
        document_repo.criar_documento.assert_called_once()

    def test_moderacao_recebe_a_amostra_de_paginas_do_pdf(self, service, bedrock_service, document_repo):
        document_repo.criar_documento.return_value = {"id": uuid4()}
        document_repo.atualizar_chave_s3.return_value = {"id": uuid4()}

        service.salvar_documento(_upload_file(), uuid4(), uuid4(), "Prova")

        bedrock_service.moderar_conteudo.assert_called_once_with(b"pdf-amostra")

    def test_moderacao_so_roda_depois_da_validacao_do_arquivo(self, service, bedrock_service):
        with pytest.raises(ValidationNotificationError):
            service.salvar_documento(_upload_file(filename="prova.txt"), uuid4(), uuid4(), "Prova")

        bedrock_service.moderar_conteudo.assert_not_called()


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
    def test_apaga_arquivos_do_documento_e_depois_o_banco(self, service, document_repo, s3_service):
        usuario_id, documento_id = uuid4(), uuid4()
        s3_service.build_document_prefix.return_value = "usuarios/u/d/"
        document_repo.deletar_documento.return_value = True

        service.deletar_documento(documento_id, usuario_id)

        s3_service.build_document_prefix.assert_called_once_with(str(usuario_id), str(documento_id))
        s3_service.delete_prefix.assert_called_once_with("usuarios/u/d/")
        document_repo.deletar_documento.assert_called_once_with(documento_id, usuario_id)

    def test_quando_nao_encontrado_levanta_document_not_found_error(self, service, document_repo):
        document_repo.deletar_documento.return_value = False

        with pytest.raises(DocumentNotFoundError):
            service.deletar_documento(uuid4(), uuid4())

    def test_falha_no_s3_nao_apaga_o_banco(self, service, document_repo, s3_service):
        s3_service.delete_prefix.side_effect = StorageError("falha")

        with pytest.raises(StorageError):
            service.deletar_documento(uuid4(), uuid4())

        document_repo.deletar_documento.assert_not_called()


class TestDeletarPasta:
    def test_com_sucesso_nao_levanta_erro(self, service, document_repo):
        document_repo.deletar_pasta.return_value = True

        service.deletar_pasta(uuid4(), uuid4())

    def test_quando_nao_encontrada_levanta_document_not_found_error(self, service, document_repo):
        document_repo.deletar_pasta.return_value = False

        with pytest.raises(DocumentNotFoundError):
            service.deletar_pasta(uuid4(), uuid4())


class TestBuscarDocumentos:
    def test_tem_mais_quando_ha_itens_alem_da_pagina(self, service, document_repo):
        document_repo.buscar_documentos.return_value = {"itens": [{"id": uuid4()}], "total": 45}

        resultado = service.buscar_documentos(uuid4(), "sono", 20, 20)

        assert resultado["total"] == 45
        assert resultado["tem_mais"] is True

    def test_nao_tem_mais_na_ultima_pagina(self, service, document_repo):
        document_repo.buscar_documentos.return_value = {"itens": [], "total": 40}

        resultado = service.buscar_documentos(uuid4(), "", 20, 20)

        assert resultado["tem_mais"] is False

    def test_delega_termo_e_paginacao_ao_repositorio(self, service, document_repo):
        document_repo.buscar_documentos.return_value = {"itens": [], "total": 0}
        usuario_id = uuid4()

        service.buscar_documentos(usuario_id, "chicago", 10, 5)

        document_repo.buscar_documentos.assert_called_once_with(usuario_id, "chicago", 10, 5)


class TestObterArquivoBytes:
    def test_retorna_bytes_do_arquivo_do_s3(self, service, document_repo, s3_service):
        import io

        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": "doc.pdf"}
        s3_service.download_file.return_value = io.BytesIO(b"%PDF-conteudo")

        assert service.obter_arquivo_bytes(uuid4(), uuid4()) == b"%PDF-conteudo"
        s3_service.download_file.assert_called_once_with("doc.pdf")

    def test_documento_inexistente_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = None

        with pytest.raises(DocumentNotFoundError):
            service.obter_arquivo_bytes(uuid4(), uuid4())

    def test_documento_sem_chave_s3_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": None}

        with pytest.raises(DocumentNotFoundError):
            service.obter_arquivo_bytes(uuid4(), uuid4())
