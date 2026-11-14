#!/usr/bin/env bash
set -euo pipefail

# Uso: ./scripts/bump-version.sh <fix|minor|normal>
#   fix    -> incrementa la ultima cifra (patch)
#   minor  -> incrementa la cifra de en medio (minor)
#   normal -> incrementa la primera cifra (major) para saltos grandes
#
# Despues de actualizar la version, reconstruye las imagenes Docker y las
# publica en el registry indicado.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REGISTRY="${REGISTRY:-192.168.1.169:5000}"
BACKEND_IMAGE="${BACKEND_IMAGE:-mediateca-backend}"
WEB_IMAGE="${WEB_IMAGE:-mediateca-madrid-web}"
VERSION_FILE="$ROOT_DIR/VERSION"
PYPROJECT_FILE="$ROOT_DIR/backend/pyproject.toml"
PACKAGE_FILE="$ROOT_DIR/frontend/package.json"

usage() {
  echo "Uso: $0 <fix|minor|normal>" >&2
  echo "  fix    incrementa la ultima cifra" >&2
  echo "  minor  incrementa la cifra de en medio" >&2
  echo "  normal incrementa la primera cifra" >&2
  exit 1
}

if [[ $# -ne 1 ]]; then
  usage
fi

BUMP_TYPE="$1"
case "$BUMP_TYPE" in
  fix | minor | normal) ;;
  *) usage ;;
esac

if [[ -f "$VERSION_FILE" ]]; then
  CURRENT_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
else
  CURRENT_VERSION="$(sed -nE 's/^version = "([0-9]+\.[0-9]+\.[0-9]+)"/\1/p' "$PYPROJECT_FILE" | head -n1)"
fi

if [[ ! "$CURRENT_VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  echo "Version no valida: '$CURRENT_VERSION'. Se esperaba MAJOR.MINOR.PATCH." >&2
  exit 1
fi

MAJOR="${BASH_REMATCH[1]}"
MINOR="${BASH_REMATCH[2]}"
PATCH="${BASH_REMATCH[3]}"

case "$BUMP_TYPE" in
  fix)
    PATCH=$((PATCH + 1))
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  normal)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

echo "Version: ${CURRENT_VERSION} -> ${NEW_VERSION} (${BUMP_TYPE})"

printf '%s\n' "$NEW_VERSION" > "$VERSION_FILE"

sed -i -E "s/^version = \"[0-9]+\.[0-9]+\.[0-9]+\"/version = \"${NEW_VERSION}\"/" "$PYPROJECT_FILE"

if grep -qE '^[[:space:]]*"version": "[0-9]+\.[0-9]+\.[0-9]+"' "$PACKAGE_FILE"; then
  sed -i -E "s/(^[[:space:]]*\"version\": \")[0-9]+\.[0-9]+\.[0-9]+\"/\1${NEW_VERSION}\"/" "$PACKAGE_FILE"
else
  echo "No se encontro la version en $PACKAGE_FILE" >&2
  exit 1
fi

BACKEND_TAG="${REGISTRY}/${BACKEND_IMAGE}:${NEW_VERSION}"
WEB_TAG="${REGISTRY}/${WEB_IMAGE}:${NEW_VERSION}"
BACKEND_LATEST="${REGISTRY}/${BACKEND_IMAGE}:latest"
WEB_LATEST="${REGISTRY}/${WEB_IMAGE}:latest"

echo "Construyendo imagen backend: ${BACKEND_TAG}"
docker build -t "$BACKEND_TAG" -t "$BACKEND_LATEST" "$ROOT_DIR/backend"

echo "Construyendo imagen web: ${WEB_TAG}"
docker build -t "$WEB_TAG" -t "$WEB_LATEST" "$ROOT_DIR/frontend"

echo "Subiendo imagenes a ${REGISTRY}"
docker push "$BACKEND_TAG"
docker push "$BACKEND_LATEST"
docker push "$WEB_TAG"
docker push "$WEB_LATEST"

echo "Hecho: ${NEW_VERSION} publicado en ${REGISTRY}"
