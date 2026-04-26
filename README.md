# manage-vehicles

API REST para gerenciamento de veículos com autenticação JWT e conversão de câmbio USD -> BRL.

## Requisitos

- Python 3.12+
- Docker

## Configuração

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Gere uma chave secreta e substitua `SECRET_KEY` no `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Executar

```bash
# Subir PostgreSQL e Redis
docker compose up -d

# Rodar migrations
alembic upgrade head

# Criar usuários iniciais
python scripts/seed.py

# Iniciar API
uvicorn app.main:app --reload
```

Documentação interativa: http://localhost:8000/docs

Usuários criados pelo seed:

| E-mail | Senha | Perfil |
|---|---|---|
| admin@example.com | admin123 | ADMIN |
| user@example.com | user123 | USER |

## Testes

```bash
pytest
```

Para ver a cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `DATABASE_URL` | URL do PostgreSQL async | — |
| `TEST_DATABASE_URL` | URL do banco de testes | — |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379/0` |
| `SECRET_KEY` | Chave JWT (hex de 32 bytes) | — |
| `ALGORITHM` | Algoritmo JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do token em minutos | `30` |
| `EXCHANGE_API_PRIMARY` | URL da API primária de câmbio | awesomeapi |
| `EXCHANGE_API_FALLBACK` | URL da API de fallback de câmbio | frankfurter |
| `EXCHANGE_CACHE_TTL` | TTL do cache de câmbio em segundos | `300` |
