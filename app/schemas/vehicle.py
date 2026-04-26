from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class VehicleCreate(BaseModel):
    brand: str = Field(..., min_length=1, max_length=100, examples=["Toyota"])
    model: str = Field(..., min_length=1, max_length=100, examples=["Corolla"])
    year: int = Field(..., ge=1886, le=2100, examples=[2022])
    color: str = Field(..., min_length=1, max_length=50, examples=["Silver"])
    license_plate: str = Field(..., min_length=1, max_length=10, examples=["ABC1D23"])
    price_usd: Decimal = Field(..., gt=0, decimal_places=2, examples=[["25000.00"]])


class VehicleUpdate(VehicleCreate):
    pass


class VehiclePatch(BaseModel):
    brand: str | None = Field(None, min_length=1, max_length=100, examples=["Honda"])
    model: str | None = Field(None, min_length=1, max_length=100, examples=["Civic"])
    year: int | None = Field(None, ge=1886, le=2100, examples=[2023])
    color: str | None = Field(None, min_length=1, max_length=50, examples=["Black"])
    license_plate: str | None = Field(None, min_length=1, max_length=10, examples=["XYZ9W87"])
    price_usd: Decimal | None = Field(None, gt=0, decimal_places=2, examples=[["22000.00"]])


class VehicleOut(BaseModel):
    id: UUID
    brand: str
    model: str
    year: int
    color: str
    license_plate: str
    price_usd: Decimal = Field(..., decimal_places=2)
    price_brl: Decimal | None = Field(None, decimal_places=2)
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("price_usd", "price_brl")
    def serialize_decimal(self, v: Decimal | None) -> float | None:
        if v is None:
            return None
        return float(round(v, 2))


class VehicleFilters(BaseModel):
    brand: str | None = None
    year: int | None = None
    color: str | None = None
    min_price_usd: Decimal | None = None
    max_price_usd: Decimal | None = None


class BrandReport(BaseModel):
    brand: str
    total: int
