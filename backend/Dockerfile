FROM python:3.12.2-slim-bullseye

ARG ENVIRONMENT

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    PATH="$PATH:/root/.local/bin"

WORKDIR /app

RUN pip install poetry==${POETRY_VERSION}

COPY pyproject.toml poetry.lock ./

RUN if [ "${ENVIRONMENT}" = "LOCAL" ]; \
    then poetry install --no-root --no-interaction --no-ansi; \
    else poetry install --no-root --no-dev --no-interaction --no-ansi; \
    fi

RUN poetry install --only-root --no-interaction --no-ansi \
    && rm -rf "${POETRY_CACHE_DIR}"

COPY . ./

CMD ["python", "minerva/main.py"]