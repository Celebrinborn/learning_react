# Dev container - builds on same base as prod, adds dev tools
FROM python:slim

WORKDIR /workspace/src/backend

# Install build dependencies (same as prod)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install prod dependencies + dev tools
COPY src/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir debugpy black isort mypy

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=dev

EXPOSE 8000
