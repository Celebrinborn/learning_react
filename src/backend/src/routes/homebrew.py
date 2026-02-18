import logging
from typing import List

from fastapi import APIRouter, HTTPException, Security
from opentelemetry import trace

from builder import AppBuilder
from dependencies import authenticate, require_cnf_roles
from models.auth.roles import UserRole
from models.auth.user_principal import Principal
from models.homebrew import HomebrewDocument, HomebrewDocumentSummary, HomebrewTreeNode
from storage.homebrew import HomebrewStorage
from telemetry import get_tracer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/homebrew", tags=["Homebrew"])

# Create storage instance at module load
_builder = AppBuilder()
_homebrew_storage = HomebrewStorage(_builder.build_homebrew_blob_storage())

# @router.get("/me_is_dm")
# async def me_is_dm(
#     user: Principal = Security(authenticate),
#     _: Principal = Security(require_cnf_roles([[UserRole.DM]]))
# ) -> dict[str, bool]:
#     """Check if the current user has DM role."""
#     return {"is_dm": True}


@router.get("", response_model=List[HomebrewDocumentSummary])
async def list_documents(
    _0: Principal = Security(authenticate),
    _1: Principal = Security(require_cnf_roles([[UserRole.PLAYER, UserRole.DM]])),
):
    """List all available homebrew documents"""
    tracer = get_tracer()
    with tracer.start_as_current_span("list_homebrew_documents_handler"):
        return await _homebrew_storage.list_homebrew_documents()


@router.get("/tree", response_model=List[HomebrewTreeNode])
async def get_document_tree(
    _0: Principal = Security(authenticate),
    _1: Principal = Security(require_cnf_roles([[UserRole.PLAYER, UserRole.DM]])),
):
    """Get the homebrew document tree structure with subdirectories"""
    tracer = get_tracer()
    with tracer.start_as_current_span("get_homebrew_tree_handler"):
        return await _homebrew_storage.list_homebrew_tree()


@router.get("/{doc_id:path}", response_model=HomebrewDocument)
async def get_document(
    doc_id: str,
    _0: Principal = Security(authenticate),
    _1: Principal = Security(require_cnf_roles([[UserRole.PLAYER, UserRole.DM]])),
):
    """Get a specific homebrew document by ID (supports subdirectory paths)"""
    tracer = get_tracer()
    with tracer.start_as_current_span("get_homebrew_document_handler") as span:
        span.set_attribute("document.id", doc_id)
        document = await _homebrew_storage.get_homebrew_document(doc_id)
        if not document:
            span.set_status(
                trace.Status(trace.StatusCode.ERROR, "Homebrew document not found")
            )
            raise HTTPException(status_code=404, detail="Homebrew document not found")
        return document
