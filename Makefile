SHELL := /bin/bash

.PHONY: help up down build logs ps check-schema test lint fmt shell

help: ## Mostrar la ayuda
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up: ## Levantar API y portal (requiere la red mediateca de enrich)
	docker compose up -d --build

down: ## Detener los servicios
	docker compose down

build: ## Construir las imagenes
	docker compose build

logs: ## Ver logs en vivo
	docker compose logs -f --tail=100

ps: ## Estado de los servicios
	docker compose ps

openapi: ## Exportar openapi.json al repositorio compartido
	docker compose run --rm --no-deps -T api python scripts/export_openapi.py - > ../mediateca-madrid-shared/contracts/openapi.json

check-schema: ## Verificar la version del esquema compartido
	docker compose run --rm --no-deps api python -c "from mediateca.core.db import check_schema; check_schema(); print('schema ok')"

test: ## Ejecutar pytest
	docker compose run --rm --no-deps api pytest -q

lint: ## Ejecutar ruff
	docker compose run --rm --no-deps api ruff check src tests

fmt: ## Formatear con ruff
	docker compose run --rm --no-deps api ruff format src tests

shell: ## Abrir shell en la API
	docker compose exec api bash
