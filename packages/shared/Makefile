.PHONY: help test lint build

help: ## Mostrar ayuda
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

test: ## Ejecutar tests
	pytest -q

lint: ## Ejecutar ruff
	ruff check src tests

build: ## Construir wheel
	python -m build
