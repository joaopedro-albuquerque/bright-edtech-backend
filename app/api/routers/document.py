from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from app.schemas.user_schema import Pasta, PastaBase
from app.services.DocumentGeneratorService import DocumentGeneratorService
from app.api.dependencies import get_document_generator_service

router = APIRouter(prefix="/document", tags=["document"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_pastas(pasta: PastaBase, service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.criar_pasta_service(pasta)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def salvar_documento(
    documento: UploadFile = File(...),
    pasta_id: UUID = Form(...),
    user_id: UUID = Form(...),
    nome_documento: str = Form(...),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.salvar_documento(documento, pasta_id, user_id, nome_documento)


