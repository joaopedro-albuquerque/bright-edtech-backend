import io
import markdown as markdown_lib
from xhtml2pdf import pisa
from pathlib import Path

# Se este script for o pdf_generator.py dentro de /services,
# .parent.parent aponta para o diretório raiz (app) que contém 'services' e 'static'
CAMINHO_BASE = Path(__file__).resolve().parent.parent 
CAMINHO_FONTE = CAMINHO_BASE / "static" / "fonts" / "DM_Sans" / "dm-sans-black.ttf"

def aplicar_marcacao_dagua(html_content: str) -> str:
    watermark_html = """
<div style="position:absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); 
font-size: 40pt; font-family: 'DM Sans'; font-weight: 900; color: #1d4ed8; opacity: 0.5;
white-space: nowrap; text-transform: uppercase; letter-spacing: 1px; z-index: -1;">
Bright EdTech
</div>
<div style="position:absolute; bottom: 2cm; right: 1cm; font-size: 7pt; color: #999; font-family: Helvetica, Arial, sans-serif; z-index: -1;">
https://app.edtech.bright.com.br/resumos
</div>
"""
    return html_content + watermark_html

_TEMPLATE = """
<html>
<head>
<style>
@font-face {{
    font-family: 'DM Sans';
    src: url('{caminho_fonte}'); 
    font-weight: 900;
}}

@page {{ size: A4; margin: 2.2cm 1.8cm; }}
body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 11pt; color: #1a1a1a; line-height: 1.5; }}
h1 {{ font-size: 20pt; color: #16324f; border-bottom: 2px solid #16324f; padding-bottom: 8px; margin-bottom: 16px; }}
h2 {{ font-size: 15pt; color: #16324f; margin-top: 22px; margin-bottom: 8px; }}
h3 {{ font-size: 12.5pt; color: #2c5282; margin-top: 16px; margin-bottom: 6px; }}
p {{ margin: 6px 0; text-align: justify; }}
ul, ol {{ margin: 6px 0; padding-left: 20px; }}
li {{ margin: 3px 0; }}
strong {{ color: #16324f; }}
blockquote {{
margin: 10px 0; padding: 8px 14px; border-left: 3px solid #a0aec0;
background-color: #f7fafc; font-style: italic; color: #4a5568;
}}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
th, td {{ border: 1px solid #cbd5e0; padding: 7px 10px; text-align: left; font-size: 10pt; }}
th {{ background-color: #16324f; color: #ffffff; }}
tr:nth-child(even) {{ background-color: #f7fafc; }}
hr {{ border: none; border-top: 1px solid #cbd5e0; margin: 16px 0; }}
.fq-header {{ color: #718096; font-size: 9pt; margin-bottom: 18px; }}
</style>
</head>
<body>
<p class="fq-header">Bright EdTech &mdash; {titulo}</p>
{corpo_html}
</body>
</html>
"""

def gerar_pdf_de_markdown(markdown_texto: str, titulo: str) -> bytes:
    corpo_html = markdown_lib.markdown(
        markdown_texto, 
        extensions=["tables", "fenced_code"]
    )
    
    html_formatado = _TEMPLATE.format(
        titulo=titulo, 
        corpo_html=corpo_html,
        caminho_fonte=CAMINHO_FONTE.as_posix()
    )
    
    html_completo = aplicar_marcacao_dagua(html_formatado)
    
    buffer = io.BytesIO()
    resultado = pisa.CreatePDF(src=html_completo, dest=buffer)
    
    if resultado.err:
        raise RuntimeError(f"Falha ao gerar PDF a partir do markdown (código {resultado.err}).")
    
    return buffer.getvalue()