from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import get_db
from app.services import DocumentGenerator

router = APIRouter(prefix="/document", tags=["document"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_documento(
    documento: UploadFile = File(...),
    pasta: str = Form(...),
    subpasta: str = Form(...),
    nome_documento: str = Form(...),
    conn=Depends(get_db),
):
    """Recebe documento, nome do novo documento, pasta e subpasta para processamento."""
    if not documento.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O documento é obrigatório")

    # TODO: implementar o fluxo de DocumentGenerator
    # 1. salvar o arquivo no S3
    # 2. processar com IA
    # 3. salvar resultado no S3 e no banco
    # O DocumentGenerator ainda não foi implementado.
    
    return {
        "message": "Documento recebido",
        "filename": documento.filename,
        "nome_documento": nome_documento,
        "folder": pasta,
        "subfolder": subpasta,
    }
