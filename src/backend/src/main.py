from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from routes import map_router, character_router, homebrew_router, auth_router
from telemetry import setup_telemetry
from telemetry.config import instrument_fastapi
from log_config import setup_logging
from middleware import TraceResponseMiddleware

# Setup structured logging
setup_logging()

# Initialize OpenTelemetry
setup_telemetry()

# API Tags for documentation grouping
tags_metadata = [
    {
        "name": "Map Locations",
        "description": "Operations for managing map locations. Create, read, update, and delete map markers and points of interest.",
    },
    {
        "name": "Characters",
        "description": "Operations for managing characters. Create, read, update, and delete player characters and NPCs.",
    },
    {
        "name": "Homebrew",
        "description": "Operations for accessing homebrew content documents.",
    },
]

app = FastAPI(
    title="DND Stats Sheet API",
    description="Backend API for DND Stats Sheet application",
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Add trace response middleware (adds X-Trace-ID header to all responses)
app.add_middleware(TraceResponseMiddleware)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(map_router)
app.include_router(character_router)
app.include_router(homebrew_router)
app.include_router(auth_router)

# Instrument FastAPI with OpenTelemetry
instrument_fastapi(app)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "DND Stats Sheet API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
