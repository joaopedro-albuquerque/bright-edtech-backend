from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user_id, get_revisao_service
from app.schemas.revisao_schema import AvaliarRequest, AvaliarResponse, DailyMixResponse, ItemRevisaoResponse
from app.services.RevisaoService import RevisaoService

router = APIRouter(prefix="/revisoes", tags=["revisoes"])


@router.get("/hoje", response_model=DailyMixResponse, status_code=status.HTTP_200_OK)
def buscar_revisoes_hoje(
    usuario_id: UUID = Depends(get_current_user_id),
    service: RevisaoService = Depends(get_revisao_service),
) -> DailyMixResponse:
    return service.buscar_daily_mix(usuario_id)


@router.get("/flashcards", response_model=list[ItemRevisaoResponse], status_code=status.HTTP_200_OK)
def buscar_flashcards_pendentes(
    usuario_id: UUID = Depends(get_current_user_id),
    service: RevisaoService = Depends(get_revisao_service),
) -> list:
    return service.buscar_flashcards_pendentes(usuario_id)


@router.get("/quizzes", response_model=list[ItemRevisaoResponse], status_code=status.HTTP_200_OK)
def buscar_quizzes_pendentes(
    usuario_id: UUID = Depends(get_current_user_id),
    service: RevisaoService = Depends(get_revisao_service),
) -> list:
    return service.buscar_quizzes_pendentes(usuario_id)


@router.put("/cartoes/{cartao_id}/avaliar", response_model=AvaliarResponse, status_code=status.HTTP_200_OK)
def avaliar_cartao(
    cartao_id: UUID,
    payload: AvaliarRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: RevisaoService = Depends(get_revisao_service),
):
    try:
        return service.avaliar_cartao(cartao_id, usuario_id, payload.qualidade)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/questoes/{questao_id}/avaliar", response_model=AvaliarResponse, status_code=status.HTTP_200_OK)
def avaliar_questao(
    questao_id: UUID,
    payload: AvaliarRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: RevisaoService = Depends(get_revisao_service),
):
    try:
        return service.avaliar_questao(questao_id, usuario_id, payload.qualidade)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
