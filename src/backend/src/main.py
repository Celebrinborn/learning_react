from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from dnd_backend.routes import map_router, character_router

# Load environment variables
load_dotenv()

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
]

app = FastAPI(
    title="DND Stats Sheet API",
    description="Backend API for DND Stats Sheet application",
    version="1.0.0",
    openapi_tags=tags_metadata
)

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
