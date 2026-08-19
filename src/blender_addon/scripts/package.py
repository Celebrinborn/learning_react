"""Build the installable Blender extension ZIP for Hex Heightmap Generator.

The ZIP must contain ``blender_manifest.toml`` and the Python package at
its root (Blender extension packaging model). Tests, env, dist, and
bytecode are excluded.

Usage:
    python scripts/package.py            # prints the ZIP path
    (imported by scripts/run_integration.py)
"""

from __future__ import annotations

from pathlib import Path
import sys
import zipfile

ADDON_ROOT: Path = Path(__file__).resolve().parent.parent
PACKAGE_DIR: Path = ADDON_ROOT / "hex_heightmap_generator"
DIST_DIR: Path = ADDON_ROOT / "dist"
ZIP_NAME: str = "hex_heightmap_generator-0.1.0.zip"

# Directories never shipped inside the extension ZIP.
EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".git", "__pycache__", "env", "dist", "tests", ".pytest_cache"}
)
# File suffixes never shipped.
EXCLUDED_SUFFIXES: frozenset[str] = frozenset({".pyc", ".pyo"})


def _iter_package_files() -> list[Path]:
    """Return every shippable file under the package directory."""
    files: list[Path] = []
    for path in sorted(PACKAGE_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def build_zip(force: bool = False) -> Path:
    """Build (or reuse) the extension ZIP and return its path."""
    zip_path: Path = DIST_DIR / ZIP_NAME
    if zip_path.is_file() and not force:
        return zip_path
    if not (PACKAGE_DIR / "blender_manifest.toml").is_file():
        raise FileNotFoundError(
            f"manifest not found: {PACKAGE_DIR / 'blender_manifest.toml'}"
        )
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    files: list[Path] = _iter_package_files()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            arcname: str = file_path.relative_to(ADDON_ROOT).as_posix()
            zf.write(file_path, arcname)
    return zip_path


if __name__ == "__main__":
    try:
        built: Path = build_zip(force=True)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print(str(built))
