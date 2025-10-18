FROM python:3.12-slim-trixie AS build


RUN apt-get update && apt-get install -y --no-install-recommends \
    git openssh-client ca-certificates build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

FROM python:3.12-slim-trixie AS runtime

ENV VIRTUAL_ENV=/opt/venv \
    PYTHONUNBUFFERED=1
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN useradd -u 10001 -m appuser

WORKDIR /app

COPY --from=build /app/.venv /opt/venv
COPY --from=build /app /app

RUN mkdir -p /var/lib/hr/media \
    && chown -R appuser:appuser /var/lib/hr

USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
