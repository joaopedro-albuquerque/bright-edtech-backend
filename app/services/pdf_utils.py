import io
import logging

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

PAGINAS_POR_TRECHO_MODERACAO = 2


def _abrir_leitor(file_stream) -> PdfReader:
    try:
        file_stream.seek(0)
        leitor = PdfReader(file_stream)
        len(leitor.pages)
        return leitor
    except Exception as e:
        logger.error(f"Falha ao ler o binário do PDF: {str(e)}", exc_info=True)
        raise ValueError("O arquivo PDF está corrompido ou é ilegível.")


def contar_paginas(file_stream) -> int:
    try:
        return len(_abrir_leitor(file_stream).pages)
    finally:
        file_stream.seek(0)


def ler_bytes(file_stream) -> bytes:
    file_stream.seek(0)
    conteudo = file_stream.read()
    file_stream.seek(0)
    return conteudo


def amostrar_paginas(file_stream) -> bytes:
    """Novo PDF só com início, meio e fim do original: moderação barata sem mandar o documento inteiro."""
    try:
        leitor = _abrir_leitor(file_stream)
        total = len(leitor.pages)
        n = PAGINAS_POR_TRECHO_MODERACAO

        if total <= 3 * n:
            indices = list(range(total))
        else:
            inicio_meio = total // 2 - n // 2
            indices = sorted(
                set(range(n)) | set(range(inicio_meio, inicio_meio + n)) | set(range(total - n, total))
            )

        escritor = PdfWriter()
        for i in indices:
            escritor.add_page(leitor.pages[i])
        saida = io.BytesIO()
        escritor.write(saida)
        return saida.getvalue()
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Falha ao amostrar páginas do PDF: {str(e)}", exc_info=True)
        raise ValueError("O arquivo PDF está corrompido ou é ilegível.")
    finally:
        file_stream.seek(0)
