from decimal import Decimal
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from unittest.mock import AsyncMock

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleFilters, VehiclePatch, VehicleUpdate
from app.services.vehicle_service import VehicleService


def make_vehicle(**kwargs) -> Vehicle:
    v = Vehicle()
    v.id = uuid4()
    v.brand = kwargs.get("brand", "Toyota")
    v.model = kwargs.get("model", "Corolla")
    v.year = kwargs.get("year", 2022)
    v.color = kwargs.get("color", "White")
    v.license_plate = kwargs.get("license_plate", "ABC1234")
    v.price_usd = Decimal(kwargs.get("price_usd", "10000.00"))
    v.active = True
    now = datetime.now(timezone.utc)
    v.created_at = now
    v.updated_at = now
    return v


@pytest.mark.asyncio
async def test_create_vehicle_duplicate_license_plate_raises_409():
    mock_repo = AsyncMock()
    mock_repo.get_by_license_plate.return_value = make_vehicle()

    service = VehicleService(mock_repo)

    with pytest.raises(HTTPException) as exc_info:
        await service.create(VehicleCreate(
            brand="Honda", model="Civic", year=2021,
            color="Black", license_plate="ABC1234", price_usd=Decimal("15000"),
        ))

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_list_combined_filters():
    mock_repo = AsyncMock()
    mock_repo.get_all.return_value = ([], 0)

    service = VehicleService(mock_repo)
    filters = VehicleFilters(brand="Toyota", year=2022, color="White")
    await service.list(filters=filters, page=1, size=20, order_by="created_at", order_dir="desc", exchange_rate=5.0)

    passed_filters = mock_repo.get_all.call_args.kwargs["filters"]
    assert passed_filters.brand == "Toyota"
    assert passed_filters.year == 2022
    assert passed_filters.color == "White"


def test_put_invalid_payload_raises_validation_error():
    with pytest.raises(ValidationError):
        VehicleUpdate(
            brand="", model="Corolla", year=2022,
            color="White", license_plate="ABC1234", price_usd=Decimal("10000"),
        )


def test_patch_invalid_payload_raises_validation_error():
    with pytest.raises(ValidationError):
        VehiclePatch(year=1800)
