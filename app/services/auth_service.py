from fastapi import HTTPException

from app.core.security import create_access_token, verify_password
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return TokenResponse(access_token=token)
