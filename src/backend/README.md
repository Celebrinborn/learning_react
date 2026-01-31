# DND Stats Sheet Backend API

FastAPI backend server for the DND Stats Sheet application.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

5. Edit `.env` with your configuration.

## Running the Server

### Development Mode (with auto-reload):
```bash
python src/main.py
```

Or using uvicorn directly:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Available Endpoints

### General
- `GET /` - Root endpoint
- `GET /health` - Health check

### Map Locations
- `POST /api/map-locations` - Create a map location
- `GET /api/map-locations` - List all map locations (optional ?map_id filter)
- `GET /api/map-locations/{location_id}` - Get specific map location
- `PUT /api/map-locations/{location_id}` - Update a map location
- `DELETE /api/map-locations/{location_id}` - Delete a map location

### Characters
- `POST /api/characters` - Create a character
- `GET /api/characters` - List all characters
- `GET /api/characters/{character_id}` - Get specific character
- `PUT /api/characters/{character_id}` - Update a character
- `DELETE /api/characters/{character_id}` - Delete a character

## Project Structure

```
backend/
├── src/
│   ├── main.py              # Main FastAPI application
│   ├── routes/              # Route handlers organized by feature
│   │   ├── map.py          # Map location endpoints
│   │   └── character.py    # Character endpoints
│   ├── models/              # Pydantic models organized by feature
│   │   ├── map.py          # Map location models
│   │   └── character.py    # Character models
│   └── storage/             # Data storage layer organized by feature
│       ├── map.py          # Map location storage operations
│       └── character.py    # Character storage operations
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Environment variables (create this)
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Next Steps

- Add database models and connection
- Implement authentication
- Add more endpoints for character management
- Integrate with Azure Blob Storage for file uploads
- Add testing
