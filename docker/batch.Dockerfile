FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

COPY packages/shared /app/packages/shared
RUN pip install --upgrade pip && pip install /app/packages/shared

COPY .env.example .
COPY services/enrich/pyproject.toml services/enrich/README.md ./
COPY services/enrich/src ./src
COPY services/enrich/scripts ./scripts
COPY services/enrich/fixtures ./fixtures
COPY services/enrich/tests ./tests

RUN pip install -e ".[dev]"

CMD ["python", "-m", "mediateca", "worker"]
