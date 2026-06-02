import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.api.dependencies import get_profile_service, get_dashboard_service
from app.services.ProfileService import ProfileService
from app.services.DashboardService import DashboardService
from app.schemas.user_schema import Usuario, UsuarioBase
from app.schemas.dashboard_schema import DashboardResponse
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(prefix="/profile", tags=["profile"])

def extrair_cognito_id(token: str) -> str:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        cognito_id = payload.get("sub")
        
        if not cognito_id:
            raise ValueError("Claim 'sub' ausente no token.")
            
        return cognito_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token JWT inválido ou malformado."
        )

@router.post("/", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    usuario: UsuarioBase, 
    service: ProfileService = Depends(get_profile_service)
) -> Usuario:
    return service.criar_usuario(usuario)

@router.get("/", response_model=Usuario, status_code=status.HTTP_200_OK)
def buscar_usuario_por_cognito_id(
    token: str = Depends(oauth2_scheme), 
    service: ProfileService = Depends(get_profile_service)
) -> Usuario:
    
    cognito_id = extrair_cognito_id(token)
    usuario = service.buscar_usuario_por_cognito_id(cognito_id)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado no banco de dados."
        )
        
    return usuario

@router.get("/{user_id}", response_model=Usuario, status_code=status.HTTP_200_OK)
def buscar_usuario_por_id(user_id: UUID, service: ProfileService = Depends(get_profile_service)) -> Usuario:
    usuario = service.buscar_usuario_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario

@router.put("/{user_id}", response_model=Usuario, status_code=status.HTTP_200_OK)
def atualizar_usuario_por_id(user_id: UUID, usuario: UsuarioBase, service: ProfileService = Depends(get_profile_service)) -> Usuario:
    usuario_atualizado = service.atualizar_usuario_por_id(user_id, usuario)
    if not usuario_atualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario_atualizado

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_usuario_por_id(user_id: UUID, service: ProfileService = Depends(get_profile_service)) -> None:
    deleted = service.deletar_usuario_por_id(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return None

@router.get("/{user_id}/dashboard", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
def obter_dashboard(user_id: UUID, service: DashboardService = Depends(get_dashboard_service)) -> DashboardResponse:
    return service.obter_dashboard_usuario(user_id)