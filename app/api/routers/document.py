from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.schemas.user_schema import Pasta, PastaBase, PastaConteudoResponse, PastaListagemResponse
from app.services.DocumentGeneratorService import DocumentGeneratorService
from app.api.dependencies import get_current_user_id, get_document_generator_service

pastas_router = APIRouter(prefix="/pastas", tags=["pastas"])
documentos_router = APIRouter(prefix="/documentos", tags=["documentos"])
resumos_router = APIRouter(prefix="/resumos", tags=["resumos"])


@pastas_router.post("", status_code=status.HTTP_201_CREATED)
async def criar_pasta(
    pasta: PastaBase, 
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.criar_pasta_service(pasta)


@pastas_router.get("/user/{user_id}", response_model=list[PastaListagemResponse], status_code=status.HTTP_200_OK)
def listar_pastas_raiz(
    user_id: UUID, 
    limit: int = Query(50, ge=1, le=100),  
    offset: int = Query(0, ge=0), 
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> list:
    return service.listar_pastas_raiz_por_usuario(user_id, limit, offset)


@pastas_router.get("/user/{user_id}/todas", response_model=list[PastaListagemResponse], status_code=status.HTTP_200_OK)
def listar_todas_pastas_usuario(
    user_id: UUID,
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> list:
    return service.listar_todas_pastas_por_usuario(user_id)


@pastas_router.get("/{pasta_id}/conteudo", response_model=PastaConteudoResponse, status_code=status.HTTP_200_OK)
def listar_conteudo_pasta(
    pasta_id: UUID,
    limit: int = Query(50, ge=1, le=100),  
    offset: int = Query(0, ge=0),         
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.listar_conteudo_pasta(pasta_id, limit, offset)


@pastas_router.put("/{pasta_id}", response_model=Pasta, status_code=status.HTTP_200_OK)
def atualizar_pasta(
    pasta_id: UUID, 
    nome: str = Form(...), 
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> Pasta:
    pasta_atualizada = service.atualizar_pasta_nome(pasta_id, nome)
    if not pasta_atualizada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pasta não encontrada")
    return pasta_atualizada


@pastas_router.delete("/{pasta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pasta(
    pasta_id: UUID, 
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> None:
    deleted = service.deletar_pasta(pasta_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pasta não encontrada")
    return None

@documentos_router.post("/upload", status_code=status.HTTP_201_CREATED)
def salvar_documento(
    documento: UploadFile = File(...),
    pasta_id: UUID = Form(...),
    user_id: UUID = Form(...),
    nome_documento: str = Form(...),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    return service.salvar_documento(documento, pasta_id, user_id, nome_documento)


@documentos_router.get("/{documento_id}/url-visualizacao", status_code=status.HTTP_200_OK)
def obter_url_visualizacao(
    documento_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
) -> dict:
    try:
        url = service.gerar_pre_signed_url_visualizacao(documento_id, usuario_id)
        return {"url": url}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

@resumos_router.post("", status_code=status.HTTP_201_CREATED)
def gerar_documento(
    usuario_id: UUID = Form(...),
    pasta_id: UUID = Form(...),
    arquivo:  UUID = Form(...),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    resultado = service.processar_novo_documento(usuario_id, pasta_id, arquivo)
    return resultado


@resumos_router.get("/{arquivo}", status_code=status.HTTP_200_OK)
def buscar_resumo(
    arquivo: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DocumentGeneratorService = Depends(get_document_generator_service)
):
    try:
        return service.buscar_resumo_documento(arquivo, usuario_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))