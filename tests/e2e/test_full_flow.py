import pytest
from unittest.mock import AsyncMock, patch

ADMIN_CREDENTIALS = {"email": "e2e_admin@test.com", "password": "admin123"}


@pytest.mark.asyncio
async def test_full_admin_flow(client, db_session):
    from app.core.security import hash_password
    from app.models.user import RoleEnum, User

    admin = User(
        email=ADMIN_CREDENTIALS["email"],
        hashed_password=hash_password("admin123"),
        role=RoleEnum.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()

    # 1. Obter token
    token_response = await client.post("/auth/token", json=ADMIN_CREDENTIALS)
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Criar veículo (ADMIN)
    create_response = await client.post(
        "/veiculos",
        json={"brand": "Tesla", "model": "Model 3", "year": 2023, "color": "Red", "license_plate": "E2E0001", "price_usd": "35000.00"},
        headers=headers,
    )
    assert create_response.status_code == 201
    vehicle_id = create_response.json()["id"]

    # 3. Listar veículos
    with patch("app.api.v1.vehicles.get_usd_to_brl_rate", new=AsyncMock(return_value=5.0)):
        list_response = await client.get("/veiculos", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

    # 4. Filtrar por marca
    with patch("app.api.v1.vehicles.get_usd_to_brl_rate", new=AsyncMock(return_value=5.0)):
        filter_response = await client.get("/veiculos?brand=Tesla", headers=headers)
    assert filter_response.status_code == 200
    assert any(v["license_plate"] == "E2E0001" for v in filter_response.json()["items"])

    # 5. Detalhar veículo
    with patch("app.api.v1.vehicles.get_usd_to_brl_rate", new=AsyncMock(return_value=5.0)):
        detail_response = await client.get(f"/veiculos/{vehicle_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["price_brl"] is not None
