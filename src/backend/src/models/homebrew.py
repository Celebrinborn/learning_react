from pydantic import BaseModel
from typing import List, Literal, Optional


class HomebrewDocumentSummary(BaseModel):
    """Summary model for listing homebrew documents"""
    id: str
    title: str


class HomebrewDocument(BaseModel):
    """Model representing a full homebrew document with content"""
    id: str
    title: str
    content: str


class HomebrewTreeNode(BaseModel):
    """A node in the homebrew file tree. Can be a file or a directory."""
    name: str
    type: Literal["file", "directory"]
    path: str
    children: Optional[List["HomebrewTreeNode"]] = None
