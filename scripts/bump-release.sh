#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
  local code="${1:-1}"
  cat >&2 <<'EOF'
Uso: bump-release.sh <major|minor|fix> [opciones]

Incrementa la version, reconstruye las imagenes mediateca-batch y
mediateca-web, y las publica en el registro con la etiqueta de version y
latest.

Opciones:
  --no-cache   Reconstruye las imagenes sin usar la cache de Docker.
  -h, --help   Muestra esta ayuda.

Variables de entorno:
  REGISTRY     Registro de destino (por defecto 192.168.1.169:5000).
  BATCH_IMAGE  Nombre de la imagen de ingesta (por defecto mediateca-batch).
  WEB_IMAGE    Nombre de la imagen web (por defecto mediateca-web).
EOF
  exit "$code"
}

BUMP_TYPE=""
NO_CACHE=0

for arg in "$@"; do
  case "$arg" in
    major | minor | fix) BUMP_TYPE="$arg" ;;
    --no-cache) NO_CACHE=1 ;;
    -h | --help) usage 0 ;;
    *)
      echo "Opcion no valida: $arg" >&2
      usage
      ;;
  esac
done

if [[ -z "$BUMP_TYPE" ]]; then
  usage
fi

echo "==> Incrementando version (${BUMP_TYPE})"
./scripts/bump-version.sh "$BUMP_TYPE"

VERSION="$(tr -d '[:space:]' < VERSION)"
export REGISTRY="${REGISTRY:-192.168.1.169:5000}"
export NO_CACHE

echo "==> Reconstruyendo y publicando imagenes ${VERSION} en ${REGISTRY}"
./scripts/release.sh

echo "==> Listo: ${REGISTRY}/mediateca-batch:${VERSION} y ${REGISTRY}/mediateca-web:${VERSION}"
