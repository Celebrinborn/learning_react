# Local Development Guide

This document describes how to set up and run the DND Stats Sheet application locally for development.

## Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend build tools
- **Docker** (optional) - For containerized development

## Project Structure

```
DND Stats Sheet React/
├── src/
│   ├── backend/           # FastAPI Python backend
│   │   ├── src/
│   │   │   ├── main.py           # Application entry point
│   │   │   ├── config.py         # Environment configuration
│   │   │   ├── builder.py        # Dependency injection
│   │   │   ├── routes/           # API endpoints
│   │   │   ├── storage/          # Business logic
│   │   │   ├── providers/        # Storage implementations
│   │   │   ├── interfaces/       # Abstract interfaces
│   │   │   └── models/           # Pydantic models
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── frontend/          # React + Vite frontend
│       ├── src/
│       ├── package.json
│       ├── nginx.conf
│       └── Dockerfile
│
├── data/                  # Local data directory (dev environment)
│   ├── maps/             # Map location JSON files
│   ├── characters/       # Character JSON files
│   ├── users/            # User data
│   └── homebrew/         # Homebrew markdown files
│
└── docs/                  # Documentation
```

## Environment Configuration

The application uses environment-based configuration controlled by `APP_ENV`:

| Environment | Storage | Auth | Use Case |
|-------------|---------|------|----------|
| `dev` | Local files (`./data/`) | Fake auth | Local development |
| `prod` | Azure Blob Storage | Microsoft Entra ID | Production |

## Backend Setup

### 1. Create Virtual Environment

```bash
cd src/backend
python -m venv env

# Windows
.\env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Backend

```bash
# Set environment (optional, defaults to dev)
set APP_ENV=dev  # Windows
export APP_ENV=dev  # Linux/Mac

# Run with uvicorn
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at `http://127.0.0.1:8000`.

### API Documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Frontend Setup

### 1. Install Dependencies

```bash
cd src/frontend
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 3. Build for Production

```bash
npm run build
```

Build output will be in `src/frontend/dist/`.

## Data Directory

The `./data/` directory stores all application data in local development:

### Maps (`data/maps/`)

JSON files representing map locations:

```json
{
  "id": "uuid",
  "name": "Location Name",
  "description": "Description text",
  "latitude": 45.0,
  "longitude": -122.0,
  "map_id": "map-uuid",
  "icon_type": "city"
}
```

### Characters (`data/characters/`)

JSON files with character data (UUID-based filenames).

### Homebrew (`data/homebrew/`)

Markdown files with custom D&D rules and content:

```
data/homebrew/
├── custom-races.md
├── spell-homebrew.md
└── subclasses/
    └── fighter-variants.md
```

## Docker Development

### Build Images

```bash
# Backend
docker build -t dnd-backend:dev -f src/backend/Dockerfile src/backend

# Frontend
docker build -t dnd-frontend:dev -f src/frontend/Dockerfile src/frontend
```

### Run with Docker Compose

Create a `docker-compose.yml` in the project root:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=dev
    volumes:
      - ./data:/app/data

  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
```

Run with:

```bash
docker-compose up --build
```

## Testing

### Backend Tests

```bash
cd src/backend
pytest
```

With coverage:

```bash
pytest --cov=src --cov-report=html
```

### Frontend Tests

```bash
cd src/frontend
npm test
```

## Common Tasks

### Adding a New API Endpoint

1. Create/update model in `src/backend/src/models/`
2. Create/update storage class in `src/backend/src/storage/`
3. Create/update router in `src/backend/src/routes/`
4. Register router in `src/backend/src/main.py`

### Adding a New Storage Type

1. Create provider in `src/backend/src/providers/` implementing `IBlobStorage`
2. Add builder method in `src/backend/src/builder.py`
3. Add configuration in `src/backend/src/config.py`

## Troubleshooting

### Backend Won't Start

- Check Python version: `python --version` (need 3.11+)
- Ensure virtual environment is activated
- Verify all dependencies installed: `pip install -r requirements.txt`

### Frontend Build Fails

- Check Node version: `node --version` (need 18+)
- Clear cache: `rm -rf node_modules && npm install`

### CORS Errors

- Ensure backend is running on the expected port
- Check `CORS_ORIGINS` in config.py for dev environment
- Frontend dev server proxies `/api` to backend automatically

### Data Not Persisting

- Verify `APP_ENV=dev` is set
- Check `./data/` directory exists and has correct permissions
- Look for error messages in backend console output
