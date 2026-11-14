FROM node:22-bookworm-slim AS web-build

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

FROM node:22-bookworm-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY packages/shared /app/packages/shared
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install /app/packages/shared

COPY services/api/pyproject.toml services/api/README.md ./api/
COPY services/api/src ./api/src
COPY services/api/scripts ./api/scripts
COPY services/api/tests ./api/tests

RUN cd /app/api && /opt/venv/bin/pip install -e ".[dev]"

COPY --from=web-build /app/.next/standalone ./web
COPY --from=web-build /app/.next/static ./web/.next/static
COPY --from=web-build /app/public ./web/public

WORKDIR /app/web

EXPOSE 3000

CMD ["node", "server.js"]
