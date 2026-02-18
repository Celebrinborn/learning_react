from fastapi import APIRouter, HTTPException
from typing import List
from opentelemetry import trace

from models.homebrew import HomebrewDocument, HomebrewDocumentSummary, HomebrewTreeNode
from storage.homebrew import HomebrewStorage
from builder import AppBuilder
from telemetry import get_tracer

router = APIRouter(prefix="/api/homebrew", tags=["Homebrew"])

# Create storage instance at module load
_builder = AppBuilder()
_homebrew_storage = HomebrewStorage(_builder.build_homebrew_blob_storage())


@router.get("", response_model=List[HomebrewDocumentSummary])
async def list_documents():
    """List all available homebrew documents"""
    tracer = get_tracer()
    with tracer.start_as_current_span("list_homebrew_documents_handler"):
        return await _homebrew_storage.list_homebrew_documents()


@router.get("/tree", response_model=List[HomebrewTreeNode])
async def get_document_tree():
    """Get the homebrew document tree structure with subdirectories"""
    tracer = get_tracer()
    with tracer.start_as_current_span("get_homebrew_tree_handler"):
        return await _homebrew_storage.list_homebrew_tree()


@router.get("/{doc_id:path}", response_model=HomebrewDocument)
async def get_document(doc_id: str):
    """Get a specific homebrew document by ID (supports subdirectory paths)"""
    tracer = get_tracer()
    with tracer.start_as_current_span("get_homebrew_document_handler") as span:
        span.set_attribute("document.id", doc_id)
        document = await _homebrew_storage.get_homebrew_document(doc_id)
        if not document:
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Homebrew document not found"))
            raise HTTPException(status_code=404, detail="Homebrew document not found")
        return document
