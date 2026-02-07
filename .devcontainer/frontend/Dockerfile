# Dev container - builds on same base as prod, for vite dev server
FROM node:slim

WORKDIR /workspace/src/frontend

# Install git for dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (same as prod)
COPY src/frontend/package.json src/frontend/package-lock.json* /tmp/frontend/
RUN cd /tmp/frontend && npm ci

EXPOSE 5173
