SHELL := /bin/bash

q ?= cine
pages ?= 1
limit ?= 20

.PHONY: help up down build logs ps init demo harvest index refresh test lint fmt shell psql clean

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up: ## Levantar PostgreSQL, Meilisearch, API y portal
	docker compose up -d --build

down: ## Detener los servicios
	docker compose down

build: ## Construir las imagenes
	docker compose build

logs: ## Ver logs en vivo
	docker compose logs -f --tail=100

ps: ## Estado de los servicios
	docker compose ps

init: ## Crear tablas e indice de busqueda
	docker compose exec api mediateca init-db

demo: ## Cargar dos fichas de ejemplo (DVD y Blu-ray) e indexar
	docker compose exec api mediateca demo --index

harvest: ## Recolectar del OPAC: make harvest q=cine pages=2 limit=20
	docker compose exec api mediateca harvest --query "$(q)" --max-pages $(pages) $(if $(limit),--limit $(limit),)

index: ## Indexar todas las ediciones en Meilisearch
	docker compose exec api mediateca index

refresh: ## Refrescar disponibilidad
	docker compose exec api mediateca refresh-availability --limit $(limit)

test: ## Ejecutar pytest dentro del contenedor
	docker compose exec api pytest -q

lint: ## Ejecutar ruff
	docker compose exec api ruff check src tests

fmt: ## Formatear con ruff
	docker compose exec api ruff format src tests

shell: ## Abrir shell en el backend
	docker compose exec api bash

psql: ## Abrir psql en PostgreSQL
	docker compose exec db psql -U $${POSTGRES_USER:-mediateca} -d $${POSTGRES_DB:-mediateca}

clean: ## Detener y borrar volumenes (destructivo)
	docker compose down -v
