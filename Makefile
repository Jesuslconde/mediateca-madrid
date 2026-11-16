SHELL := /bin/bash

q ?= cine
pages ?= 1
limit ?= 20
branches_limit ?=

.PHONY: help up down build logs ps init migrate harvest branches index dashboard dashboard-logs worker-logs test test-shared test-api test-enrich lint fmt shell psql openapi web-types contracts check-schema bump bump-release release clean

help: ## Mostrar la ayuda
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: ## Levantar el stack completo
	docker compose up -d --build

down: ## Detener los servicios
	docker compose down

build: ## Construir las dos imagenes
	docker compose build

logs: ## Ver logs en vivo
	docker compose logs -f --tail=100

ps: ## Estado de los servicios
	docker compose ps

init: ## Crear tablas, aplicar migraciones e indexar
	docker compose run --rm init

migrate: ## Aplicar migraciones idempotentes
	docker compose run --rm --no-deps worker python -m mediateca migrate

harvest: ## Recolectar del OPAC: make harvest q=cine pages=2 limit=20
	docker compose run --rm worker python -m mediateca harvest --query "$(q)" --max-pages $(pages) $(if $(limit),--limit $(limit),)

branches: ## Actualizar sucursales desde el directorio: make branches branches_limit=20
	docker compose run --rm worker python -m mediateca refresh-branches $(if $(branches_limit),--limit $(branches_limit),)

index: ## Indexar todas las ediciones
	docker compose run --rm worker python -m mediateca index

dashboard: ## Levantar el dashboard de estado
	docker compose up -d dashboard

dashboard-logs: ## Ver logs del dashboard
	docker compose logs -f --tail=100 dashboard

worker-logs: ## Ver logs del worker
	docker compose logs -f --tail=100 worker

test: test-shared test-api test-enrich ## Ejecutar todas las pruebas Python

test-shared: ## Ejecutar las pruebas del paquete compartido
	docker compose run --rm --no-deps worker pytest /app/packages/shared/tests -q

test-api: ## Ejecutar las pruebas de la API
	docker compose run --rm --no-deps -w /app/api api /opt/venv/bin/pytest -q

test-enrich: ## Ejecutar las pruebas de ingesta
	docker compose run --rm --no-deps worker pytest -q

lint: ## Ejecutar ruff en API e ingesta
	docker compose run --rm --no-deps -w /app/api api /opt/venv/bin/ruff check src tests
	docker compose run --rm --no-deps worker ruff check src tests /app/packages/shared/src /app/packages/shared/tests

fmt: ## Formatear con ruff
	docker compose run --rm --no-deps -w /app/api api /opt/venv/bin/ruff format src tests
	docker compose run --rm --no-deps worker ruff format src tests /app/packages/shared/src /app/packages/shared/tests

shell: ## Abrir shell en el worker
	docker compose exec worker bash

psql: ## Abrir psql
	docker compose exec db psql -U $${POSTGRES_USER:-mediateca} -d $${POSTGRES_DB:-mediateca}

openapi: ## Exportar el contrato OpenAPI a contracts/openapi.json
	./scripts/export-openapi.sh

web-types: ## Regenerar los tipos TypeScript del portal
	cd apps/web && npm run generate:api

contracts: openapi web-types ## Regenerar contrato y tipos del portal

check-schema: ## Verificar la version del esquema compartido
	docker compose run --rm --no-deps api /opt/venv/bin/python -c "from mediateca.core.db import check_schema; check_schema(); print('schema ok')"

bump: ## Incrementar version: make bump type=major|minor|fix
	./scripts/bump-version.sh "$(type)"

bump-release: ## Incrementar, reconstruir y publicar: make bump-release type=fix
	./scripts/bump-release.sh "$(type)"

release: ## Construir y publicar las imagenes con la version actual
	./scripts/release.sh

clean: ## Detener y borrar volumenes (destructivo)
	docker compose down -v
