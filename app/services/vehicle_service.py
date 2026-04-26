from __future__ import annotations

import logging
import math
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.repositories.vehicle_repo import VehicleRepository
from app.schemas.vehicle import (
    BrandReport,
    VehicleCreate,
    VehicleFilters,
    VehicleOut,
    VehiclePatch,
    VehicleUpdate,
)
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)


class VehicleService:
    def __init__(self, repo: VehicleRepository) -> None:
        self.repo = repo

    async def list(
        self,
        filters: VehicleFilters,
        page: int,
        size: int,
        order_by: str,
        order_dir: str,
        exchange_rate: float,
    ) -> PaginatedResponse[VehicleOut]:
        items, total = await self.repo.get_all(
            filters=filters, page=page, size=size,
            order_by=order_by, order_dir=order_dir,
        )
        vehicles_out = [self._to_out(v, exchange_rate) for v in items]
        pages = math.ceil(total / size) if size else 1
        return PaginatedResponse(items=vehicles_out, total=total, page=page, size=size, pages=pages)

    async def get_by_id(self, vehicle_id: UUID, exchange_rate: float) -> VehicleOut:
        vehicle = await self.repo.get_by_id(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        return self._to_out(vehicle, exchange_rate)

    async def create(self, data: VehicleCreate, exchange_rate: float) -> VehicleOut:
        existing = await self.repo.get_by_license_plate(data.license_plate)
        if existing is not None:
            logger.warning("Tentativa de cadastro com placa duplicada: %s", data.license_plate)
            raise HTTPException(status_code=409, detail="Placa já cadastrada")
        vehicle = await self.repo.create(data)
        logger.info("Veículo cadastrado: id=%s placa=%s", vehicle.id, vehicle.license_plate)
        return self._to_out(vehicle, exchange_rate)

    async def update(self, vehicle_id: UUID, data: VehicleUpdate) -> VehicleOut:
        vehicle = await self.repo.get_by_id(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        if data.license_plate != vehicle.license_plate:
            await self._check_license_plate(data.license_plate, vehicle_id)
        updated = await self.repo.update(vehicle, data.model_dump())
        logger.info("Veículo atualizado (PUT): id=%s", vehicle_id)
        return VehicleOut.model_validate(updated)

    async def patch(self, vehicle_id: UUID, data: VehiclePatch) -> VehicleOut:
        vehicle = await self.repo.get_by_id(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        patch_data = data.model_dump(exclude_none=True)
        if "license_plate" in patch_data and patch_data["license_plate"] != vehicle.license_plate:
            await self._check_license_plate(patch_data["license_plate"], vehicle_id)
        updated = await self.repo.update(vehicle, patch_data)
        logger.info("Veículo atualizado (PATCH): id=%s campos=%s", vehicle_id, list(patch_data.keys()))
        return VehicleOut.model_validate(updated)

    async def delete(self, vehicle_id: UUID) -> None:
        vehicle = await self.repo.get_by_id(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        await self.repo.soft_delete(vehicle)
        logger.info("Veículo removido (soft delete): id=%s placa=%s", vehicle_id, vehicle.license_plate)

    async def report_by_brand(self) -> list[BrandReport]:
        rows = await self.repo.count_by_brand()
        return [BrandReport(**row) for row in rows]

    async def _check_license_plate(self, license_plate: str, exclude_id: UUID) -> None:
        existing = await self.repo.get_by_license_plate(license_plate)
        if existing is not None and existing.id != exclude_id:
            logger.warning("Tentativa de atualização com placa duplicada: %s", license_plate)
            raise HTTPException(status_code=409, detail="Placa já cadastrada")

    def _to_out(self, vehicle, exchange_rate: float) -> VehicleOut:
        out = VehicleOut.model_validate(vehicle)
        out.price_brl = round(vehicle.price_usd * Decimal(str(exchange_rate)), 2)
        return out
