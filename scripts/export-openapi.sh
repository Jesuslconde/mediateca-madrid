#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p contracts
docker compose run --rm --no-deps -T api /opt/venv/bin/python /app/api/scripts/export_openapi.py > contracts/openapi.json
echo "Contrato actualizado en contracts/openapi.json"
