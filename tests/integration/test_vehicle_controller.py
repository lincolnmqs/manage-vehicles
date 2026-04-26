import pytest
from unittest.mock import AsyncMock, patch

VEHICLE_PAYLOAD = {
    "brand": "Toyota",
    "model": "Corolla",
    "year": 2022,
    "color": "White",
    "license_plate": "TST0099",
    "price_usd": "10000.00",
}


@pytest.mark.asyncio
async def test_list_vehicles_no_token_returns_401(client):
    response = await client.get("/veiculos")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_vehicle_user_forbidden_returns_403(client, user_token):
    response = await client.post(
        "/veiculos",
        json=VEHICLE_PAYLOAD,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_vehicle_duplicate_license_plate_returns_409(client, admin_token):
    payload = {**VEHICLE_PAYLOAD, "license_plate": "DUP0099"}
    await client.post("/veiculos", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    response = await client.post("/veiculos", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_error_payload_is_standardized(client, admin_token):
    payload = {**VEHICLE_PAYLOAD, "license_plate": "STD0099"}
    await client.post("/veiculos", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    response = await client.post("/veiculos", json=payload, headers={"Authorization": f"Bearer {admin_token}"})

    body = response.json()
    assert "detail" in body
    assert "code" in body
    assert "status" in body
