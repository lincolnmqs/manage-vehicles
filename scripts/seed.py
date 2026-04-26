import asyncio

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import RoleEnum, User


async def seed():
    async with AsyncSessionLocal() as session:
        users = [
            User(
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                role=RoleEnum.ADMIN,
            ),
            User(
                email="user@example.com",
                hashed_password=hash_password("user123"),
                role=RoleEnum.USER,
            ),
        ]
        session.add_all(users)
        await session.commit()
        print("Usuários criados: admin@example.com / user@example.com")


if __name__ == "__main__":
    asyncio.run(seed())
