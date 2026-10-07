from uuid import uuid4

import pytest

from app.core.exceptions import DocumentNotFoundError, ResumoNotFoundError
from app.services.ResumoService import ResumoService


@pytest.fixture
def resumo_repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def document_repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def s3_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def bedrock_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def service(resumo_repo, document_repo, s3_service, bedrock_service):
    return ResumoService(resumo_repo, document_repo, s3_service, bedrock_service)


class TestGerarResumo:
    def test_com_sucesso_gera_resumo_e_pdf(
        self, service, document_repo, s3_service, bedrock_service, resumo_repo, mocker
    ):
        mocker.patch("app.services.ResumoService.extrair_texto_do_pdf", return_value="texto extraído")
        mocker.patch("app.services.ResumoService.gerar_pdf_de_markdown", return_value=b"pdf-bytes")
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": "doc.pdf"}
        s3_service.download_file.return_value = b"pdf-bytes"
        bedrock_service.gerar_resumo.return_value = ("texto gerado", 100, "modelo-x")
        resumo_repo.criar.return_value = {"id": uuid4()}

        resultado = service.gerar_resumo(uuid4(), uuid4(), nivel_conhecimento=5, formato="cornell", tom="formal")

        assert "id" in resultado
        chamada = resumo_repo.criar.call_args
        assert chamada.kwargs["s3_chave_pdf"] is not None

    def test_quando_geracao_de_pdf_falha_usa_none_como_fallback(
        self, service, document_repo, s3_service, bedrock_service, resumo_repo, mocker
    ):
        mocker.patch("app.services.ResumoService.extrair_texto_do_pdf", return_value="texto extraído")
        mocker.patch(
            "app.services.ResumoService.gerar_pdf_de_markdown", side_effect=Exception("falha no reportlab")
        )
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = {"chave_s3": "doc.pdf"}
        s3_service.download_file.return_value = b"pdf-bytes"
        bedrock_service.gerar_resumo.return_value = ("texto gerado", 100, "modelo-x")
        resumo_repo.criar.return_value = {"id": uuid4()}

        service.gerar_resumo(uuid4(), uuid4(), nivel_conhecimento=5, formato="cornell", tom="formal")

        chamada = resumo_repo.criar.call_args
        assert chamada.kwargs["s3_chave_pdf"] is None

    def test_quando_documento_nao_encontrado_levanta_document_not_found_error(self, service, document_repo):
        document_repo.buscar_chave_s3_por_documento_id_e_usuario.return_value = None

        with pytest.raises(DocumentNotFoundError):
            service.gerar_resumo(uuid4(), uuid4(), nivel_conhecimento=5, formato="cornell", tom="formal")


def test_listar_por_documento_delega_para_repositorio(service, resumo_repo):
    resumo_repo.listar_por_documento.return_value = [{"id": uuid4()}]

    resultado = service.listar_por_documento(uuid4(), uuid4())

    assert len(resultado) == 1


class TestObterConteudo:
    def test_com_sucesso_retorna_texto_do_s3(self, service, resumo_repo, s3_service):
        resumo_repo.buscar_por_id.return_value = {"id": uuid4(), "titulo": "R", "s3_chave": "chave.md"}
        s3_service.download_text.return_value = "# conteúdo"

        resultado = service.obter_conteudo(uuid4(), uuid4())

        assert resultado["conteudo"] == "# conteúdo"

    def test_quando_nao_encontrado_levanta_erro(self, service, resumo_repo):
        resumo_repo.buscar_por_id.return_value = None

        with pytest.raises(ResumoNotFoundError):
            service.obter_conteudo(uuid4(), uuid4())


class TestObterDownloadUrl:
    def test_com_pdf_ja_existente_retorna_url_direto(self, service, resumo_repo, s3_service):
        resumo_repo.buscar_por_id.return_value = {
            "id": uuid4(), "titulo": "R", "s3_chave_pdf": "ja-existe.pdf",
        }
        s3_service.generate_presigned_url.return_value = "https://s3/url"

        resultado = service.obter_download_url(uuid4(), uuid4())

        assert resultado == "https://s3/url"
        s3_service.download_text.assert_not_called()

    def test_sem_pdf_existente_gera_na_hora_e_persiste_chave(self, service, resumo_repo, s3_service, mocker):
        mocker.patch("app.services.ResumoService.gerar_pdf_de_markdown", return_value=b"pdf-bytes")
        resumo_repo.buscar_por_id.return_value = {
            "id": uuid4(), "titulo": "R", "s3_chave_pdf": None,
            "s3_chave": "chave.md", "documento_id": uuid4(), "formato": "cornell",
        }
        s3_service.download_text.return_value = "# conteúdo"
        s3_service.generate_presigned_url.return_value = "https://s3/url"

        resultado = service.obter_download_url(uuid4(), uuid4())

        assert resultado == "https://s3/url"
        resumo_repo.atualizar_s3_chave_pdf.assert_called_once()

    def test_quando_nao_encontrado_levanta_erro(self, service, resumo_repo):
        resumo_repo.buscar_por_id.return_value = None

        with pytest.raises(ResumoNotFoundError):
            service.obter_download_url(uuid4(), uuid4())


class TestRenomearResumo:
    def test_com_sucesso_retorna_resumo_atualizado(self, service, resumo_repo):
        resumo_repo.atualizar_titulo.return_value = {"titulo": "Novo"}

        resultado = service.renomear_resumo(uuid4(), uuid4(), "Novo")

        assert resultado["titulo"] == "Novo"

    def test_quando_nao_encontrado_levanta_erro(self, service, resumo_repo):
        resumo_repo.atualizar_titulo.return_value = None

        with pytest.raises(ResumoNotFoundError):
            service.renomear_resumo(uuid4(), uuid4(), "Novo")


class TestDeletarResumo:
    def test_com_sucesso_nao_levanta_erro(self, service, resumo_repo):
        resumo_repo.deletar.return_value = True

        service.deletar_resumo(uuid4(), uuid4())

    def test_quando_nao_encontrado_levanta_erro(self, service, resumo_repo):
        resumo_repo.deletar.return_value = False

        with pytest.raises(ResumoNotFoundError):
            service.deletar_resumo(uuid4(), uuid4())
