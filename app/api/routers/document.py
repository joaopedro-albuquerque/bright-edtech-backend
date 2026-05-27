from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.schemas.user_schema import Pasta, PastaBase, PastaConteudoResponse, PastaListagemResponse
from app.services.DocumentGeneratorService import DocumentGeneratorService
from app.api.dependencies import get_document_generator_service

router = APIRouter(prefix="/document", tags=["document"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_pastas(pasta: PastaBase, service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.criar_pasta_service(pasta)

@router.get("/pastas/user/{user_id}", response_model=list[PastaListagemResponse], status_code=status.HTTP_200_OK)
def listar_pastas_raiz(
    user_id: UUID, 
    limit: int = 50, 
    offset: int = 0, 
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> list:
    return service.listar_pastas_raiz_por_usuario(user_id, limit, offset)

@router.get("/{pasta_id}/conteudo", response_model=PastaConteudoResponse, status_code=status.HTTP_200_OK)
def listar_conteudo_pasta(
    pasta_id: UUID,
    limit: int = Query(50, ge=1, le=100),  
    offset: int = Query(0, ge=0),         
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.listar_conteudo_pasta(pasta_id, limit, offset)

@router.put("/pastas/{pasta_id}", response_model=Pasta, status_code=status.HTTP_200_OK)
def atualizar_pasta(pasta_id: UUID, nome: str = Form(...), service: DocumentGeneratorService = Depends(get_document_generator_service)) -> Pasta:
    pasta_atualizada = service.atualizar_pasta_nome(pasta_id, nome)
    if not pasta_atualizada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pasta não encontrada")
    return pasta_atualizada


@router.delete("/pastas/{pasta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pasta(pasta_id: UUID, service: DocumentGeneratorService = Depends(get_document_generator_service)) -> None:
    deleted = service.deletar_pasta(pasta_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pasta não encontrada")
    return None



@router.post("/", status_code=status.HTTP_201_CREATED)
async def salvar_documento(
    documento: UploadFile = File(...),
    pasta_id: UUID = Form(...),
    user_id: UUID = Form(...),
    nome_documento: str = Form(...),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.salvar_documento(documento, pasta_id, user_id, nome_documento)