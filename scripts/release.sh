#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="$(tr -d '[:space:]' < VERSION)"
REGISTRY="${REGISTRY:-192.168.1.169:5000}"
BATCH_IMAGE="${BATCH_IMAGE:-mediateca-batch}"
WEB_IMAGE="${WEB_IMAGE:-mediateca-web}"

BATCH_TAG="${REGISTRY}/${BATCH_IMAGE}:${VERSION}"
BATCH_LATEST="${REGISTRY}/${BATCH_IMAGE}:latest"
WEB_TAG="${REGISTRY}/${WEB_IMAGE}:${VERSION}"
WEB_LATEST="${REGISTRY}/${WEB_IMAGE}:latest"

echo "Construyendo ${BATCH_TAG}"
docker build -f docker/batch.Dockerfile -t "$BATCH_TAG" -t "$BATCH_LATEST" .

echo "Construyendo ${WEB_TAG}"
docker build -f docker/web.Dockerfile -t "$WEB_TAG" -t "$WEB_LATEST" .

echo "Publicando imagenes en ${REGISTRY}"
docker push "$BATCH_TAG"
docker push "$BATCH_LATEST"
docker push "$WEB_TAG"
docker push "$WEB_LATEST"

echo "Publicado ${VERSION}"
