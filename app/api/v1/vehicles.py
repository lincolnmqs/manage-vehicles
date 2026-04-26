from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.exchange import get_usd_to_brl_rate
from app.db.session import get_db
from app.models.user import User
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
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/veiculos", tags=["veiculos"])


def get_service(db: AsyncSession = Depends(get_db)) -> VehicleService:
    return VehicleService(VehicleRepository(db))


@router.get(
    "/relatorios/por-marca",
    response_model=list[BrandReport],
    summary="Retorna relatório de quantidade de veículos agrupados por marca",
    description=(
        "Retorna a quantidade de veículos ativos agrupados por marca, em ordem decrescente.\n\n"
        "Apenas veículos com `active=true` são contabilizados (removidos via soft delete são excluídos).\n\n"
        "**Requer autenticação.** Acessível para os perfis `USER` e `ADMIN`."
    ),
)
async def report_by_brand(
    service: VehicleService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    return await service.report_by_brand()


@router.get(
    "",
    response_model=PaginatedResponse[VehicleOut],
    summary="Retorna todos os veículos",
    description=(
        "Retorna uma lista paginada de veículos ativos.\n\n"
        "**Filtros disponíveis (combináveis):**\n"
        "- `brand` — correspondência exata (ex: `Toyota`)\n"
        "- `year` — ano de fabricação (ex: `2022`)\n"
        "- `color` — correspondência exata (ex: `Prata`)\n"
        "- `minPrice` / `maxPrice` — faixa de preço **em BRL**; a conversão para USD é feita automaticamente\n\n"
        "**Paginação:** `page` (padrão 1) e `size` (padrão 20, máx 100).\n\n"
        "**Ordenação:** `order_by` (padrão `created_at`) e `order_dir` (`asc` ou `desc`).\n\n"
        "O campo `price_brl` é calculado em tempo real com a cotação atual do dólar (cache Redis 5 min).\n\n"
        "**Requer autenticação.** Acessível para os perfis `USER` e `ADMIN`."
    ),
)
async def list_vehicles(
    brand: str | None = Query(None),
    year: int | None = Query(None),
    color: str | None = Query(None),
    min_price: Decimal | None = Query(None, alias="minPrice"),
    max_price: Decimal | None = Query(None, alias="maxPrice"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: VehicleService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    exchange_rate = await get_usd_to_brl_rate()
    filters = VehicleFilters(
        brand=brand,
        year=year,
        color=color,
        min_price_usd=min_price / Decimal(str(exchange_rate)) if min_price else None,
        max_price_usd=max_price / Decimal(str(exchange_rate)) if max_price else None,
    )
    return await service.list(
        filters=filters, page=page, size=size,
        order_by=order_by, order_dir=order_dir,
        exchange_rate=exchange_rate,
    )


@router.get(
    "/{vehicle_id}",
    response_model=VehicleOut,
    summary="Retorna os detalhes do veículo",
    description=(
        "Retorna os dados de um veículo específico pelo seu UUID.\n\n"
        "O campo `price_brl` é calculado em tempo real com a cotação atual do dólar (cache Redis 5 min).\n\n"
        "Retorna `404` se o veículo não existir ou tiver sido removido via soft delete.\n\n"
        "**Requer autenticação.** Acessível para os perfis `USER` e `ADMIN`."
    ),
)
async def get_vehicle(
    vehicle_id: UUID,
    service: VehicleService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    exchange_rate = await get_usd_to_brl_rate()
    return await service.get_by_id(vehicle_id, exchange_rate)


@router.post(
    "",
    response_model=VehicleOut,
    status_code=201,
    summary="Adiciona um novo veículo",
    description=(
        "Cadastra um novo veículo no sistema.\n\n"
        "O preço deve ser informado **em USD**. O campo `price_brl` será calculado "
        "automaticamente na resposta com a cotação atual.\n\n"
        "A placa deve ser única — retorna `409` em caso de duplicidade.\n\n"
        "**Requer autenticação com perfil `ADMIN`.**"
    ),
)
async def create_vehicle(
    payload: VehicleCreate,
    service: VehicleService = Depends(get_service),
    _: User = Depends(require_admin),
):
    return await service.create(payload)


@router.put(
    "/{vehicle_id}",
    response_model=VehicleOut,
    summary="Atualiza os dados de um veículo",
    description=(
        "Substitui todos os dados de um veículo existente (atualização completa).\n\n"
        "Todos os campos obrigatórios devem ser enviados. Para atualizar apenas alguns campos, use o `PATCH`.\n\n"
        "Retorna `404` se o veículo não existir e `409` se a nova placa já estiver em uso.\n\n"
        "**Requer autenticação com perfil `ADMIN`.**"
    ),
)
async def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdate,
    service: VehicleService = Depends(get_service),
    _: User = Depends(require_admin),
):
    return await service.update(vehicle_id, payload)


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleOut,
    summary="Atualiza parcialmente os dados de um veículo",
    description=(
        "Atualiza parcialmente os dados de um veículo — envie apenas os campos que deseja alterar.\n\n"
        "Campos não enviados permanecem inalterados. Para substituir o veículo inteiro, use o `PUT`.\n\n"
        "Retorna `404` se o veículo não existir e `409` se a nova placa já estiver em uso.\n\n"
        "**Requer autenticação com perfil `ADMIN`.**"
    ),
)
async def patch_vehicle(
    vehicle_id: UUID,
    payload: VehiclePatch,
    service: VehicleService = Depends(get_service),
    _: User = Depends(require_admin),
):
    return await service.patch(vehicle_id, payload)


@router.delete(
    "/{vehicle_id}",
    status_code=204,
    summary="Remove um veículo (soft delete)",
    description=(
        "Realiza a remoção lógica (soft delete) de um veículo, marcando-o como `active=false`.\n\n"
        "O veículo não é excluído fisicamente do banco e não aparecerá mais nas listagens.\n\n"
        "Retorna `404` se o veículo não existir ou já tiver sido removido.\n\n"
        "**Requer autenticação com perfil `ADMIN`.**"
    ),
)
async def delete_vehicle(
    vehicle_id: UUID,
    service: VehicleService = Depends(get_service),
    _: User = Depends(require_admin),
):
    await service.delete(vehicle_id)
