from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Autenticação",
    description=(
        "Autentica um usuário com e-mail e senha e retorna um token JWT Bearer.\n\n"
        "O token deve ser enviado no cabeçalho `Authorization: Bearer <token>` em todas "
        "as requisições protegidas.\n\n"
        "**Roles disponíveis:**\n"
        "- `USER` — acesso somente leitura (GET)\n"
        "- `ADMIN` — acesso completo (GET, POST, PUT, PATCH, DELETE)"
    ),
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db))
    return await service.login(payload.email, payload.password)
