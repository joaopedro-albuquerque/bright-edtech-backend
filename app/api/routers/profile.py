from fastapi import APIRouter, Depends, HTTPException, Request, status
from uuid import UUID

from app.api.dependencies import get_current_user_id, get_profile_service, get_dashboard_service
from app.services.ProfileService import ProfileService
from app.services.DashboardService import DashboardService
from app.schemas.user_schema import OnboardingRequest, Usuario, UsuarioBase
from app.schemas.dashboard_schema import DashboardResponse

router = APIRouter(prefix="/profile", tags=["profile"])

def extrair_cognito_id(request: Request) -> str:
    # O AuthMiddleware (app/core/auth_middleware.py) já validou a assinatura,
    # o emissor e a expiração do token antes de a requisição chegar aqui, e
    # anexou os claims decodificados em request.state.token_claims.
    claims = getattr(request.state, "token_claims", None)
    cognito_id = claims.get("sub") if claims else None

    if not cognito_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido ou malformado."
        )

    return cognito_id

@router.post("", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    usuario: UsuarioBase,
    service: ProfileService = Depends(get_profile_service)
) -> Usuario:
    return service.criar_usuario(usuario)

@router.get("", response_model=Usuario, status_code=status.HTTP_200_OK)
def buscar_usuario_por_cognito_id(
    request: Request,
    service: ProfileService = Depends(get_profile_service)
) -> Usuario:

    cognito_id = extrair_cognito_id(request)
    usuario = service.buscar_usuario_por_cognito_id(cognito_id)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado no banco de dados."
        )
        
    return usuario
    
@router.put("", response_model=Usuario, status_code=status.HTTP_200_OK)
def atualizar_meu_perfil(
    request: Request,
    usuario_update: UsuarioBase,
    service: ProfileService = Depends(get_profile_service)
) -> Usuario:
    # 1. Extrai o ID do Cognito diretamente do token validado no request
    cognito_id = extrair_cognito_id(request)
    
    # 2. Busca o utilizador atual na base de dados para descobrir o seu UUID interno
    usuario_atual = service.buscar_usuario_por_cognito_id(cognito_id)
    
    if not usuario_atual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado no banco de dados."
        )
        
    # 3. Atualiza o perfil usando o ID interno verdadeiro (usuario_atual.id)
    usuario_atualizado = service.atualizar_usuario_por_id(usuario_atual.id, usuario_update)
    
    if not usuario_atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Erro ao atualizar o usuário."
        )
        
    return usuario_atualizado    

def _garantir_dono(user_id: UUID, usuario_id: UUID) -> None:
    if usuario_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

@router.get("/{user_id}", response_model=Usuario, status_code=status.HTTP_200_OK)
def buscar_usuario_por_id(
    user_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service)
) -> Usuario:
    _garantir_dono(user_id, usuario_id)
    usuario = service.buscar_usuario_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario

@router.put("/{user_id}", response_model=Usuario, status_code=status.HTTP_200_OK)
def atualizar_usuario_por_id(
    user_id: UUID,
    usuario: UsuarioBase,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service)
) -> Usuario:
    _garantir_dono(user_id, usuario_id)
    usuario_atualizado = service.atualizar_usuario_por_id(user_id, usuario)
    if not usuario_atualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario_atualizado

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_usuario_por_id(
    user_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service)
) -> None:
    _garantir_dono(user_id, usuario_id)
    deleted = service.deletar_usuario_por_id(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return None

@router.get("/{user_id}/dashboard", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
def obter_dashboard(
    user_id: UUID,
    usuario_id: UUID = Depends(get_current_user_id),
    service: DashboardService = Depends(get_dashboard_service)
) -> DashboardResponse:
    _garantir_dono(user_id, usuario_id)
    return service.obter_dashboard_usuario(user_id)


@router.post("/{user_id}/perfil", response_model=Usuario, status_code=status.HTTP_200_OK)
def salvar_perfil_onboarding(
    user_id: UUID,
    perfil: OnboardingRequest,
    usuario_id: UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service)
) -> Usuario:
    _garantir_dono(user_id, usuario_id)
    usuario_atualizado = service.atualizar_perfil_onboarding(user_id, perfil)
    if not usuario_atualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario_atualizado