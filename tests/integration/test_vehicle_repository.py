from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.vehicle_repo import VehicleRepository
from app.schemas.vehicle import VehicleCreate, VehicleFilters


def make_vehicle(license_plate: str = "ABC1234", price_usd: str = "10000.00") -> VehicleCreate:
    return VehicleCreate(
        brand="Toyota",
        model="Corolla",
        year=2022,
        color="White",
        license_plate=license_plate,
        price_usd=Decimal(price_usd),
    )


@pytest.mark.asyncio
async def test_unique_license_plate_constraint(db_session):
    repo = VehicleRepository(db_session)
    await repo.create(make_vehicle("DUP0001"))

    with pytest.raises(IntegrityError):
        await repo.create(make_vehicle("DUP0001"))


@pytest.mark.asyncio
async def test_filter_by_brand(db_session):
    repo = VehicleRepository(db_session)
    await repo.create(VehicleCreate(brand="Honda", model="Civic", year=2021, color="Black", license_plate="HON0001", price_usd=Decimal("15000")))
    await repo.create(VehicleCreate(brand="Ford", model="Focus", year=2020, color="Blue", license_plate="FOR0001", price_usd=Decimal("12000")))

    items, _ = await repo.get_all(filters=VehicleFilters(brand="Honda"), page=1, size=20, order_by="created_at", order_dir="desc")

    assert all(v.brand == "Honda" for v in items)


@pytest.mark.asyncio
async def test_soft_delete_excludes_from_list(db_session):
    repo = VehicleRepository(db_session)
    vehicle = await repo.create(make_vehicle("DEL0001"))
    await repo.soft_delete(vehicle)

    items, _ = await repo.get_all(filters=VehicleFilters(), page=1, size=20, order_by="created_at", order_dir="desc")

    assert vehicle.id not in [v.id for v in items]
