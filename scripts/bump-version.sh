#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
  echo "Uso: $0 <major|minor|fix>" >&2
  echo "  major  incrementa la primera cifra (major)" >&2
  echo "  minor  incrementa la cifra de en medio (minor)" >&2
  echo "  fix    incrementa la ultima cifra (patch)" >&2
  echo "  normal alias historico de major" >&2
  exit 1
}

if [[ $# -ne 1 ]]; then
  usage
fi

BUMP_TYPE="$1"
case "$BUMP_TYPE" in
  major | minor | fix | normal) ;;
  *) usage ;;
esac

CURRENT_VERSION="$(tr -d '[:space:]' < VERSION)"
if [[ ! "$CURRENT_VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  echo "Version no valida: '$CURRENT_VERSION'" >&2
  exit 1
fi

MAJOR="${BASH_REMATCH[1]}"
MINOR="${BASH_REMATCH[2]}"
PATCH="${BASH_REMATCH[3]}"

case "$BUMP_TYPE" in
  fix) PATCH=$((PATCH + 1)) ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  major | normal) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "Version: ${CURRENT_VERSION} -> ${NEW_VERSION} (${BUMP_TYPE})"

printf '%s\n' "$NEW_VERSION" > VERSION

python3 - "$NEW_VERSION" <<'PY'
from pathlib import Path
import sys

version = sys.argv[1]
pyprojects = [
    Path("packages/shared/pyproject.toml"),
    Path("services/api/pyproject.toml"),
    Path("services/enrich/pyproject.toml"),
]
for path in pyprojects:
    text = path.read_text()
    for line in text.splitlines():
        if line.startswith("version = "):
            text = text.replace(line, f'version = "{version}"', 1)
            break
    path.write_text(text)

inits = [
    Path("packages/shared/src/mediateca_shared/__init__.py"),
    Path("services/api/src/mediateca/__init__.py"),
    Path("services/enrich/src/mediateca/__init__.py"),
]
for path in inits:
    lines = path.read_text().splitlines()
    for index, line in enumerate(lines):
        if line.startswith("__version__ = "):
            lines[index] = f'__version__ = "{version}"'
            break
    path.write_text("\n".join(lines) + "\n")
PY

if command -v npm >/dev/null 2>&1; then
  (cd apps/web && npm version "$NEW_VERSION" --no-git-tag-version --allow-same-version >/dev/null)
else
  echo "npm no disponible; actualiza apps/web/package.json y package-lock.json a mano" >&2
fi

echo "Version unificada actualizada a ${NEW_VERSION}"
