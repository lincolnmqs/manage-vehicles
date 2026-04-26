from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleFilters


class VehicleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(
        self,
        filters: VehicleFilters,
        page: int,
        size: int,
        order_by: str,
        order_dir: str,
    ) -> tuple[list[Vehicle], int]:
        stmt = select(Vehicle).where(Vehicle.active.is_(True))
        stmt = self._apply_filters(stmt, filters)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        column = getattr(Vehicle, order_by, Vehicle.created_at)
        stmt = stmt.order_by(column.desc() if order_dir == "desc" else column.asc())
        stmt = stmt.offset((page - 1) * size).limit(size)

        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    def _apply_filters(self, stmt, filters: VehicleFilters):
        if filters.brand:
            stmt = stmt.where(Vehicle.brand == filters.brand)
        if filters.year:
            stmt = stmt.where(Vehicle.year == filters.year)
        if filters.color:
            stmt = stmt.where(Vehicle.color == filters.color)
        if filters.min_price_usd is not None:
            stmt = stmt.where(Vehicle.price_usd >= filters.min_price_usd)
        if filters.max_price_usd is not None:
            stmt = stmt.where(Vehicle.price_usd <= filters.max_price_usd)
        return stmt

    async def get_by_id(self, vehicle_id: UUID) -> Vehicle | None:
        result = await self.session.execute(
            select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_by_license_plate(self, license_plate: str) -> Vehicle | None:
        result = await self.session.execute(
            select(Vehicle).where(Vehicle.license_plate == license_plate)
        )
        return result.scalar_one_or_none()

    async def create(self, data: VehicleCreate) -> Vehicle:
        vehicle = Vehicle(**data.model_dump())
        self.session.add(vehicle)
        await self.session.flush()
        await self.session.refresh(vehicle)
        return vehicle

    async def update(self, vehicle: Vehicle, data: dict) -> Vehicle:
        for key, value in data.items():
            setattr(vehicle, key, value)
        vehicle.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(vehicle)
        return vehicle

    async def soft_delete(self, vehicle: Vehicle) -> Vehicle:
        vehicle.active = False
        vehicle.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return vehicle

    async def count_by_brand(self) -> list[dict]:
        stmt = (
            select(Vehicle.brand, func.count(Vehicle.id).label("total"))
            .where(Vehicle.active.is_(True))
            .group_by(Vehicle.brand)
            .order_by(func.count(Vehicle.id).desc())
        )
        result = await self.session.execute(stmt)
        return [{"brand": row.brand, "total": row.total} for row in result.all()]
