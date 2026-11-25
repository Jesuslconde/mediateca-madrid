#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="$(tr -d '[:space:]' < VERSION)"
REGISTRY="${REGISTRY:-192.168.1.169:5000}"
BATCH_IMAGE="${BATCH_IMAGE:-mediateca-batch}"
WEB_IMAGE="${WEB_IMAGE:-mediateca-web}"

CONTAINER_ENGINE="${CONTAINER_ENGINE:-}"
if [[ -z "$CONTAINER_ENGINE" ]]; then
  if command -v docker >/dev/null 2>&1; then
    CONTAINER_ENGINE="docker"
  elif command -v podman >/dev/null 2>&1; then
    CONTAINER_ENGINE="podman"
  else
    echo "No se encontro docker ni podman; instala uno de los dos" >&2
    exit 1
  fi
fi

if ! command -v "$CONTAINER_ENGINE" >/dev/null 2>&1; then
  echo "El motor de contenedores no esta disponible: $CONTAINER_ENGINE" >&2
  exit 1
fi

BATCH_TAG="${REGISTRY}/${BATCH_IMAGE}:${VERSION}"
BATCH_LATEST="${REGISTRY}/${BATCH_IMAGE}:latest"
WEB_TAG="${REGISTRY}/${WEB_IMAGE}:${VERSION}"
WEB_LATEST="${REGISTRY}/${WEB_IMAGE}:latest"

BUILD_ARGS=()
if [[ "${NO_CACHE:-0}" == "1" ]]; then
  BUILD_ARGS+=(--no-cache)
fi

echo "Construyendo ${BATCH_TAG} con ${CONTAINER_ENGINE}"
"$CONTAINER_ENGINE" build "${BUILD_ARGS[@]}" -f docker/batch.Dockerfile -t "$BATCH_TAG" -t "$BATCH_LATEST" .

echo "Construyendo ${WEB_TAG} con ${CONTAINER_ENGINE}"
"$CONTAINER_ENGINE" build "${BUILD_ARGS[@]}" -f docker/web.Dockerfile -t "$WEB_TAG" -t "$WEB_LATEST" .

echo "Publicando imagenes en ${REGISTRY}"
"$CONTAINER_ENGINE" push "$BATCH_TAG"
"$CONTAINER_ENGINE" push "$BATCH_LATEST"
"$CONTAINER_ENGINE" push "$WEB_TAG"
"$CONTAINER_ENGINE" push "$WEB_LATEST"

echo "Publicado ${VERSION}"
