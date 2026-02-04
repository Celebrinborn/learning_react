from pathlib import Path
from typing import List, Optional

from models.homebrew import HomebrewDocument, HomebrewDocumentSummary, HomebrewTreeNode
from telemetry import get_tracer

# Get the data directory path (relative to project root)
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "homebrew"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _extract_title_from_markdown(content: str, filename: str) -> str:
    """Extract title from first # heading or use filename"""
    for line in content.split('\n'):
        if line.startswith('# '):
            return line[2:].strip()
    # Fallback: convert filename to title
    return filename.replace('-', ' ').replace('_', ' ').title()


def _build_tree(current_dir: Path, root_dir: Path) -> List[HomebrewTreeNode]:
    """Recursively build tree nodes for a directory."""
    nodes: List[HomebrewTreeNode] = []

    # Sort entries: directories first, then files, alphabetical
    entries = sorted(current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

    for entry in entries:
        if entry.is_dir():
            children = _build_tree(entry, root_dir)
            if children:  # Only include non-empty directories
                nodes.append(HomebrewTreeNode(
                    name=entry.name.replace('_', ' ').replace('-', ' ').title(),
                    type="directory",
                    path=str(entry.relative_to(root_dir)).replace("\\", "/"),
                    children=children,
                ))
        elif entry.suffix == '.md':
            try:
                content = entry.read_text(encoding='utf-8')
                title = _extract_title_from_markdown(content, entry.stem)
                rel_path = str(entry.relative_to(root_dir)).replace("\\", "/")
                doc_id = rel_path[:-3]  # Remove .md extension
                nodes.append(HomebrewTreeNode(
                    name=title,
                    type="file",
                    path=doc_id,
                ))
            except Exception as e:
                print(f"Error reading {entry}: {e}")

    return nodes


def list_homebrew_tree() -> List[HomebrewTreeNode]:
    """Build a tree of homebrew documents respecting subdirectories."""
    tracer = get_tracer()
    with tracer.start_as_current_span("storage.list_homebrew_tree") as span:
        if not DATA_DIR.exists():
            span.set_attribute("count", 0)
            return []

        nodes = _build_tree(DATA_DIR, DATA_DIR)
        return nodes


def list_homebrew_documents() -> List[HomebrewDocumentSummary]:
    """List all available homebrew documents"""
    tracer = get_tracer()
    with tracer.start_as_current_span("storage.list_homebrew_documents") as span:
        documents: List[HomebrewDocumentSummary] = []

        if not DATA_DIR.exists():
            span.set_attribute("count", 0)
            return documents

        for file_path in DATA_DIR.glob("*.md"):
            try:
                doc_id = file_path.stem
                content = file_path.read_text(encoding='utf-8')
                title = _extract_title_from_markdown(content, doc_id)
                documents.append(HomebrewDocumentSummary(id=doc_id, title=title))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        # Sort by title
        documents.sort(key=lambda d: d.title)
        span.set_attribute("count", len(documents))
        return documents


def get_homebrew_document(doc_id: str) -> Optional[HomebrewDocument]:
    """Get a homebrew document by ID (path relative to homebrew dir, without .md extension)"""
    tracer = get_tracer()
    with tracer.start_as_current_span("storage.get_homebrew_document") as span:
        span.set_attribute("document.id", doc_id)

        # Security: prevent path traversal
        try:
            file_path = (DATA_DIR / f"{doc_id}.md").resolve()
            if not str(file_path).startswith(str(DATA_DIR.resolve())):
                span.set_attribute("found", False)
                return None
        except (ValueError, OSError):
            span.set_attribute("found", False)
            return None

        if not file_path.exists():
            span.set_attribute("found", False)
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            title = _extract_title_from_markdown(content, file_path.stem)
            span.set_attribute("found", True)
            return HomebrewDocument(id=doc_id, title=title, content=content)
        except Exception as e:
            print(f"Error reading homebrew document {doc_id}: {e}")
            span.set_attribute("error", str(e))
            return None
