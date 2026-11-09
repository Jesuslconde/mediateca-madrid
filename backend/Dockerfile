FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY vendor ./vendor
RUN pip install --upgrade pip && pip install ./vendor/*.whl

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY tests ./tests

RUN pip install -e ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "mediateca.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
