import io
import markdown as markdown_lib
from xhtml2pdf import pisa
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor # Adicionado para garantir a cor opaca correta

# Configuração de caminhos
CAMINHO_BASE = Path(__file__).resolve().parent.parent 
CAMINHO_FONTE = CAMINHO_BASE / "static" / "fonts" / "DM_Sans" / "dm-sans-black.ttf"

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
.footer-text {{ position: absolute; bottom: 2cm; right: 1cm; font-size: 7pt; color: #999; z-index: -1; }}
</style>
</head>
<body>
    <div class="footer-text">https://brightedtech.com.br</div>
    <p class="fq-header">Bright EdTech &mdash; {titulo}</p>
    {corpo_html}
</body>
</html>
"""

def aplicar_marcacao_dagua(pdf_bytes: bytes) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    # Cor sólida e preenchida (sem opacidade que atrapalhe a leitura)
    fill_color = HexColor("#E2E5F0")
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(width, height))
        
        # Posicionamento inicial para rotacionar
        c.translate(width / 2, height / 2)
        c.rotate(45) 
        
        # SUBSTITUIÇÃO 1: Definir cor de preenchimento (Fill) em vez de contorno (Stroke)
        c.setFillColor(fill_color)
        
        # Lógica da malha da marca d'água
        span = int(max(width, height) * 1.5)
        step_x = 650 
        step_y = 250 
        
        for row, y in enumerate(range(-span, span, step_y)):
            offset_x = (step_x / 2) if row % 2 != 0 else 0
            for x in range(-span, span, step_x):
                t = c.beginText(x + offset_x - 300, y) 
                t.setFont("Helvetica-Bold", 70)
                # SUBSTITUIÇÃO 2: MODO 0 = Texto Preenchido (Fill text)
                t.setTextRenderMode(0) 
                t.textOut("BRIGHT EDTECH")
                c.drawText(t)
                
        c.save()
        packet.seek(0)
        
        # Funde a camada gerada com a página existente
        watermark_pdf = PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]
        
        # SUBSTITUIÇÃO 3: Coloca o texto principal (page) POR CIMA da marca d'água (watermark_page)
        watermark_page.merge_page(page)
        
        writer.add_page(watermark_page)

    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    return output_buffer.getvalue()

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
    
    buffer = io.BytesIO()
    
    # 1. Gera o PDF do Miolo (texto) usando xhtml2pdf
    resultado = pisa.CreatePDF(src=html_formatado, dest=buffer)
    if resultado.err:
        raise RuntimeError(f"Falha ao gerar PDF a partir do markdown (código {resultado.err}).")
    
    # 2. Injeta a Marca D'água por cima manipulando o arquivo resultante em memória
    pdf_final = aplicar_marcacao_dagua(buffer.getvalue())
    
    return pdf_final