import io

import pytest
from pypdf import PdfReader, PdfWriter

from app.services.pdf_utils import amostrar_paginas, contar_paginas, ler_bytes


def _pdf_com_paginas(n: int) -> io.BytesIO:
    escritor = PdfWriter()
    for _ in range(n):
        escritor.add_blank_page(width=200, height=200)
    saida = io.BytesIO()
    escritor.write(saida)
    saida.seek(0)
    return saida


def _largura_das_paginas(pdf_bytes: bytes) -> list[int]:
    return [int(p.mediabox.width) for p in PdfReader(io.BytesIO(pdf_bytes)).pages]


def _pdf_com_paginas_numeradas(n: int) -> io.BytesIO:
    """Cada página tem largura distinta (100 + índice) para identificar quais foram amostradas."""
    escritor = PdfWriter()
    for i in range(n):
        escritor.add_blank_page(width=100 + i, height=100)
    saida = io.BytesIO()
    escritor.write(saida)
    saida.seek(0)
    return saida


class TestContarPaginas:
    def test_retorna_total_de_paginas(self):
        assert contar_paginas(_pdf_com_paginas(7)) == 7

    def test_reposiciona_o_stream_no_inicio_apos_ler(self):
        stream = _pdf_com_paginas(2)

        contar_paginas(stream)

        assert stream.tell() == 0

    def test_arquivo_corrompido_levanta_value_error(self):
        with pytest.raises(ValueError, match="corrompido ou é ilegível"):
            contar_paginas(io.BytesIO(b"isto nao e um pdf valido"))


class TestLerBytes:
    def test_retorna_conteudo_completo_e_reposiciona_stream(self):
        stream = io.BytesIO(b"conteudo")
        stream.read(3)

        assert ler_bytes(stream) == b"conteudo"
        assert stream.tell() == 0


class TestAmostrarPaginas:
    def test_pdf_curto_e_mantido_inteiro(self):
        amostra = amostrar_paginas(_pdf_com_paginas_numeradas(5))

        assert _largura_das_paginas(amostra) == [100, 101, 102, 103, 104]

    def test_pdf_longo_fica_com_inicio_meio_e_fim(self):
        amostra = amostrar_paginas(_pdf_com_paginas_numeradas(40))

        larguras = _largura_das_paginas(amostra)
        assert larguras == [100, 101, 119, 120, 138, 139]

    def test_reposiciona_o_stream_no_inicio_apos_ler(self):
        stream = _pdf_com_paginas(10)

        amostrar_paginas(stream)

        assert stream.tell() == 0

    def test_arquivo_corrompido_levanta_value_error(self):
        with pytest.raises(ValueError, match="corrompido ou é ilegível"):
            amostrar_paginas(io.BytesIO(b"isto nao e um pdf valido"))
