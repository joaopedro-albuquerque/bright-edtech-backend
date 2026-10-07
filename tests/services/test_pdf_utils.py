import io

import pytest

from app.services.pdf_generator import gerar_pdf_de_markdown
from app.services.pdf_utils import extrair_texto_do_pdf


def test_extrair_texto_do_pdf_com_sucesso_retorna_texto_contido_no_pdf():
    pdf_bytes = gerar_pdf_de_markdown("Conteudo de teste para extracao", "Titulo")
    stream = io.BytesIO(pdf_bytes)

    resultado = extrair_texto_do_pdf(stream)

    assert "Conteudo de teste para extracao" in resultado


def test_extrair_texto_do_pdf_reposiciona_o_stream_no_inicio_apos_ler():
    pdf_bytes = gerar_pdf_de_markdown("Conteudo", "Titulo")
    stream = io.BytesIO(pdf_bytes)

    extrair_texto_do_pdf(stream)

    assert stream.tell() == 0


def test_extrair_texto_do_pdf_com_arquivo_corrompido_levanta_value_error():
    stream = io.BytesIO(b"isto nao e um pdf valido")

    with pytest.raises(ValueError, match="corrompido ou é ilegível"):
        extrair_texto_do_pdf(stream)
