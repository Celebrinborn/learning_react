"""Blender background-mode test harness for the Hex Heightmap Generator.

Usage (from src/blender_addon):
    blender --background --python scripts/run_integration.py

The harness:
1. Builds the extension ZIP (scripts/package.py) and structurally validates
   it (manifest + package present at the ZIP root).
2. Imports the extension package from source and calls register() — the
   standard headless approach, since the file-install operator requires a
   configured repository and is not reliable in background mode.
3. Runs every ``test_*`` function in tests/integration/test_*.py modules.
4. Prints a PASS/FAIL summary and exits non-zero on any failure.

Exit codes: 0 = all passed, 1 = failures, 2 = harness/setup error.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import sys
import traceback
from typing import Any, Callable, List, Tuple

ADDON_ROOT: Path = Path(__file__).resolve().parent.parent
SCRIPTS_DIR: Path = Path(__file__).resolve().parent
sys.path.insert(0, str(ADDON_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

EXTENSION_ID: str = "hex_heightmap_generator"


def _build_zip() -> Path:
    """Build the extension ZIP via scripts/package.py; return its path."""
    import package  # noqa: PLC0415  (scripts/ is on sys.path via ADDON_ROOT)

    zip_path: Path = package.build_zip()
    if not zip_path.is_file():
        raise RuntimeError(f"package.build_zip() did not produce {zip_path}")
    return zip_path


def _validate_zip(zip_path: Path) -> None:
    """Structurally validate the extension ZIP (manifest + package at root)."""
    import zipfile  # noqa: PLC0415

    with zipfile.ZipFile(zip_path) as zf:
        names: list[str] = zf.namelist()
    if f"{EXTENSION_ID}/blender_manifest.toml" not in names:
        raise RuntimeError(f"manifest missing from ZIP: {zip_path}")
    if f"{EXTENSION_ID}/__init__.py" not in names:
        raise RuntimeError(f"package __init__.py missing from ZIP: {zip_path}")


def _load_extension() -> None:
    """Import the extension package from source and register it.

    Direct import + register() is the standard headless approach; the
    file-install operator requires a configured repository and is not
    reliable in background mode.
    """
    module: Any = importlib.import_module(EXTENSION_ID)
    module.register()


def _collect_test_modules() -> List[str]:
    """Return importable module names for tests/integration/test_*.py."""
    integration_dir: Path = ADDON_ROOT / "tests" / "integration"
    modules: List[str] = []
    for path in sorted(integration_dir.glob("test_*.py")):
        modules.append(f"tests.integration.{path.stem}")
    return modules


def _run_module(module_name: str) -> Tuple[int, int, List[str]]:
    """Run all test_* functions in a module. Returns (passed, failed, failures)."""
    module: Any = importlib.import_module(module_name)
    passed: int = 0
    failed: int = 0
    failures: List[str] = []
    for name, fn in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith("test_"):
            continue
        test_fn: Callable[[], None] = fn
        try:
            test_fn()
            passed += 1
            print(f"  PASS {module_name}.{name}")
        except Exception:  # noqa: BLE001 - report any failure, keep going
            failed += 1
            detail: str = traceback.format_exc()
            failures.append(f"{module_name}.{name}:\n{detail}")
            print(f"  FAIL {module_name}.{name}")
    return passed, failed, failures


def main() -> int:
    import bpy  # noqa: PLC0415

    version: str = ".".join(str(part) for part in bpy.app.version)
    print(f"Blender version: {version}")
    try:
        zip_path: Path = _build_zip()
        print(f"Built extension: {zip_path}")
        _validate_zip(zip_path)
        print("ZIP structure valid (manifest + package at root)")
        _load_extension()
        print(f"Loaded and registered extension: {EXTENSION_ID}")
    except Exception:  # noqa: BLE001 - setup failure is a harness error
        print("HARNESS SETUP FAILED:")
        traceback.print_exc()
        return 2

    total_passed: int = 0
    total_failed: int = 0
    all_failures: List[str] = []
    for module_name in _collect_test_modules():
        try:
            passed, failed, failures = _run_module(module_name)
        except Exception:  # noqa: BLE001 - module import/collection error
            total_failed += 1
            all_failures.append(
                f"{module_name} (module error):\n{traceback.format_exc()}"
            )
            print(f"  FAIL {module_name} (module could not be imported/run)")
            continue
        total_passed += passed
        total_failed += failed
        all_failures.extend(failures)

    print("\n=== INTEGRATION SUMMARY ===")
    print(f"passed: {total_passed}")
    print(f"failed: {total_failed}")
    for failure in all_failures:
        print("\n--- FAILURE ---")
        print(failure)
    return 1 if total_failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
