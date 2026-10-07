from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.resumo_schema import (
    FormatoResumoEnum,
    ResumoConteudoResponse,
    ResumoCreateRequest,
    ResumoRenomearRequest,
    ResumoResponse,
)


class TestResumoCreateRequest:
    @pytest.mark.parametrize("formato", list(FormatoResumoEnum))
    def test_aceita_todos_os_formatos_validos(self, formato):
        request = ResumoCreateRequest(nivel_conhecimento=5, formato=formato, tom="formal")

        assert request.formato == formato

    def test_rejeita_formato_invalido(self):
        with pytest.raises(ValidationError):
            ResumoCreateRequest(nivel_conhecimento=5, formato="formato_inexistente", tom="formal")

    @pytest.mark.parametrize("nivel", [0, 10])
    def test_aceita_nivel_de_conhecimento_nos_limites(self, nivel):
        request = ResumoCreateRequest(nivel_conhecimento=nivel, formato=FormatoResumoEnum.cornell, tom="formal")

        assert request.nivel_conhecimento == nivel

    @pytest.mark.parametrize("nivel", [-1, 11])
    def test_rejeita_nivel_de_conhecimento_fora_dos_limites(self, nivel):
        with pytest.raises(ValidationError):
            ResumoCreateRequest(nivel_conhecimento=nivel, formato=FormatoResumoEnum.cornell, tom="formal")

    def test_exige_todos_os_campos_obrigatorios(self):
        with pytest.raises(ValidationError):
            ResumoCreateRequest()


class TestResumoRenomearRequest:
    def test_aceita_titulo_valido(self):
        request = ResumoRenomearRequest(titulo="Novo título")

        assert request.titulo == "Novo título"

    def test_rejeita_titulo_vazio(self):
        with pytest.raises(ValidationError):
            ResumoRenomearRequest(titulo="")


def test_resumo_response_constroi_a_partir_de_dados_validos():
    resultado = ResumoResponse(
        id=uuid4(), documento_id=uuid4(), titulo="R", formato=FormatoResumoEnum.cornell,
        nivel_conhecimento=5, tom="formal", s3_chave="chave", s3_chave_pdf=None,
        tokens_utilizados=10, modelo_ia="modelo-x", criado_em=datetime.utcnow(),
    )

    assert resultado.formato == FormatoResumoEnum.cornell


def test_resumo_conteudo_response_constroi_a_partir_de_dados_validos():
    resultado = ResumoConteudoResponse(id=uuid4(), titulo="R", conteudo="# Markdown")

    assert resultado.conteudo == "# Markdown"
