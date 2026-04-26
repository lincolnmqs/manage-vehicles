import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1 import auth, vehicles
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.redis_client import close_redis, get_redis

setup_logging(settings.log_level)

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
    await close_redis()


app = FastAPI(
    title="Manage Vehicles API",
    version="1.0.0",
    description=(
        "API REST para gerenciamento de veículos com autenticação JWT e controle de acesso por perfis.\n\n"
        "## Autenticação\n\n"
        "Utilize `POST /auth/token` para obter um token JWT. "
        "Em seguida, clique em **Authorize** (🔒) e informe `Bearer <token>`.\n\n"
        "## Perfis de acesso\n\n"
        "| Perfil | Permissões |\n"
        "|--------|------------|\n"
        "| `USER` | Somente leitura (GET) |\n"
        "| `ADMIN` | Acesso completo (GET, POST, PUT, PATCH, DELETE) |\n\n"
        "## Preços\n\n"
        "Os preços são armazenados em **USD** e convertidos para **BRL** em tempo real "
        "com a cotação atual do dólar, em cache no Redis por 5 minutos.\n\n"
        "## Soft Delete\n\n"
        "Veículos removidos não são excluídos fisicamente — são marcados como `active=false` "
        "e ocultados das listagens."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s %d %.0fms", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc.errors()), "code": "VALIDATION_ERROR", "status": 422},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "VEHICLE_NOT_FOUND",
        409: "PLATE_ALREADY_EXISTS",
        503: "EXCHANGE_UNAVAILABLE",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": code_map.get(exc.status_code, "ERROR"),
            "status": exc.status_code,
        },
    )


app.include_router(auth.router)
app.include_router(vehicles.router)
