from dataclasses import dataclass, field
from typing import List, Optional

from interfaces.blob import IBlob
from models.homebrew import HomebrewDocument, HomebrewDocumentSummary, HomebrewTreeNode
from telemetry import get_tracer


def _empty_str_list() -> list[str]:
    return []


def _empty_node_dict() -> dict[str, "_TreeBuildNode"]:
    return {}


@dataclass
class _TreeBuildNode:
    """Internal node for building the tree structure."""
    files: list[str] = field(default_factory=_empty_str_list)
    children: dict[str, "_TreeBuildNode"] = field(default_factory=_empty_node_dict)


class HomebrewStorage:
    """
    Storage service for homebrew documents.
    Uses IBlobStorage for file operations.
    """

    def __init__(self, blob_storage: IBlob):
        """
        Initialize HomebrewStorage with a blob storage backend.

        Args:
            blob_storage: IBlobStorage implementation for file operations
        """
        self._storage = blob_storage

    def _get_title_from_filename(self, filename: str) -> str:
        """Use filename as title, normalizing underscores to spaces"""
        return filename.replace('_', ' ')

    def _build_tree_from_paths(self, paths: List[str]) -> List[HomebrewTreeNode]:
        """
        Build a hierarchical tree structure from a flat list of file paths.

        Args:
            paths: List of file paths (e.g., ["dir/subdir/file.md", "other.md"])

        Returns:
            List of HomebrewTreeNode representing the tree structure
        """
        root = _TreeBuildNode()

        for path in paths:
            parts = path.split('/')
            current = root

            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # This is a file
                    current.files.append(path)
                else:
                    # This is a directory
                    if part not in current.children:
                        current.children[part] = _TreeBuildNode()
                    current = current.children[part]

        return self._build_node_to_tree_nodes(root, "")

    def _build_node_to_tree_nodes(
        self,
        node: _TreeBuildNode,
        current_path: str
    ) -> List[HomebrewTreeNode]:
        """Convert _TreeBuildNode to HomebrewTreeNode list."""
        nodes: List[HomebrewTreeNode] = []

        # Sort: directories first (alphabetically), then files (alphabetically)
        sorted_dirs = sorted(node.children.keys(), key=str.lower)
        sorted_files = sorted(node.files, key=lambda p: p.split('/')[-1].lower())

        # Add directory nodes
        for dir_name in sorted_dirs:
            dir_path = f"{current_path}/{dir_name}" if current_path else dir_name
            children = self._build_node_to_tree_nodes(node.children[dir_name], dir_path)

            if children:  # Only include non-empty directories
                nodes.append(HomebrewTreeNode(
                    name=dir_name.replace('_', ' ').replace('-', ' ').title(),
                    type="directory",
                    path=dir_path,
                    children=children,
                ))

        # Add file nodes
        for file_path in sorted_files:
            filename = file_path.split('/')[-1]
            stem = filename[:-3]  # Remove .md extension
            title = self._get_title_from_filename(stem)
            doc_id = file_path[:-3]  # Remove .md extension from full path

            nodes.append(HomebrewTreeNode(
                name=title,
                type="file",
                path=doc_id,
            ))

        return nodes

    async def list_homebrew_tree(self) -> List[HomebrewTreeNode]:
        """Build a tree of homebrew documents respecting subdirectories."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.list_homebrew_tree") as span:
            # Get all files from storage
            all_paths = await self._storage.list()

            # Filter to .md files only
            md_paths = [p for p in all_paths if p.endswith('.md')]

            if not md_paths:
                span.set_attribute("count", 0)
                return []

            nodes = self._build_tree_from_paths(md_paths)
            return nodes

    async def list_homebrew_documents(self) -> List[HomebrewDocumentSummary]:
        """List all available homebrew documents (root level only)."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.list_homebrew_documents") as span:
            documents: List[HomebrewDocumentSummary] = []

            # Get all files from storage
            all_paths = await self._storage.list()

            # Filter to .md files in root directory only (no '/' in path)
            root_md_paths = [p for p in all_paths if p.endswith('.md') and '/' not in p]

            for path in root_md_paths:
                try:
                    doc_id = path[:-3]  # Remove .md extension
                    title = self._get_title_from_filename(doc_id)
                    documents.append(HomebrewDocumentSummary(id=doc_id, title=title))
                except Exception as e:
                    print(f"Error processing {path}: {e}")

            # Sort by title
            documents.sort(key=lambda d: d.title)
            span.set_attribute("count", len(documents))
            return documents

    async def get_homebrew_document(self, doc_id: str) -> Optional[HomebrewDocument]:
        """Get a homebrew document by ID (path relative to homebrew dir, without .md)."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.get_homebrew_document") as span:
            span.set_attribute("document.id", doc_id)

            # Security: basic validation (IBlobStorage handles path traversal)
            if '..' in doc_id:
                span.set_attribute("found", False)
                return None

            path = f"{doc_id}.md"

            if not await self._storage.exists(path):
                span.set_attribute("found", False)
                return None

            try:
                data = await self._storage.read(path)
                content = data.decode('utf-8')

                # Extract filename from path for title
                filename = doc_id.split('/')[-1] if '/' in doc_id else doc_id
                title = self._get_title_from_filename(filename)

                span.set_attribute("found", True)
                return HomebrewDocument(id=doc_id, title=title, content=content)
            except Exception as e:
                print(f"Error reading homebrew document {doc_id}: {e}")
                span.set_attribute("error", str(e))
                return None
