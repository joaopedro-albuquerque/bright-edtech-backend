from types import SimpleNamespace

import pytest

from app.services.pdf_generator import aplicar_marcacao_dagua, gerar_pdf_de_markdown


def test_gerar_pdf_de_markdown_com_sucesso_retorna_bytes_de_um_pdf_valido():
    resultado = gerar_pdf_de_markdown("# Título\n\nTexto de **exemplo** com uma tabela:\n\n"
                                       "| A | B |\n|---|---|\n| 1 | 2 |\n", "Meu Título")

    assert isinstance(resultado, bytes)
    assert resultado.startswith(b"%PDF")


def test_gerar_pdf_de_markdown_levanta_runtime_error_quando_pisa_falha(mocker):
    mocker.patch(
        "app.services.pdf_generator.pisa.CreatePDF",
        return_value=SimpleNamespace(err=1),
    )

    with pytest.raises(RuntimeError, match="Falha ao gerar PDF"):
        gerar_pdf_de_markdown("# Texto", "Título")


def test_aplicar_marcacao_dagua_retorna_pdf_com_mesma_quantidade_de_paginas():
    pdf_original = gerar_pdf_de_markdown("# Conteúdo original", "Original")

    resultado = aplicar_marcacao_dagua(pdf_original)

    assert isinstance(resultado, bytes)
    assert resultado.startswith(b"%PDF")
