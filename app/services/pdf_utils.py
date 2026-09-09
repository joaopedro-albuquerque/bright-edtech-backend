import logging

import PyPDF2

logger = logging.getLogger(__name__)


def extrair_texto_do_pdf(file_stream) -> str:
    try:
        file_stream.seek(0)
        leitor_pdf = PyPDF2.PdfReader(file_stream)
        texto_extraido = ""
        for pagina in leitor_pdf.pages:
            texto_extraido += pagina.extract_text() + "\n"
        return texto_extraido.strip()
    except Exception as e:
        logger.error(f"Falha ao ler o binário do PDF: {str(e)}", exc_info=True)
        raise ValueError("O arquivo PDF está corrompido ou é ilegível.")
    finally:
        file_stream.seek(0)
