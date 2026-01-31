"""
Pytest configuration and shared test fixtures.

This file (conftest.py) is automatically discovered by pytest and provides
reusable test fixtures that can be used across all test files without imports.

WHY THIS EXISTS:
- Provides isolated temporary directories for each test run
- Prevents test pollution (tests don't interfere with each other)
- Automatic cleanup after tests complete
- DRY principle - define fixtures once, use everywhere
- No manual setup/teardown code needed in individual tests

HOW TO USE:
Just add the fixture name as a parameter to any test function:

    def test_something(temp_dir: Path):
        # temp_dir is automatically created and cleaned up
        file = temp_dir / "test.txt"
        file.write_text("data")

AVAILABLE FIXTURES:
- temp_dir: Base temporary directory (auto-cleaned)
- blob_storage_path: Temp directory for blob storage testing
- character_storage_path: Temp directory for character storage testing
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test files.
    
    Automatically cleaned up after the test completes, even if the test fails.
    Each test gets its own isolated directory to prevent conflicts.
    
    Yields:
        Path: A temporary directory that will be deleted after the test
    """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup - runs even if test fails
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def blob_storage_path(temp_dir: Path) -> Path:
    """
    Create a temporary directory for blob storage provider tests.
    
    This fixture uses the temp_dir fixture, so it gets automatic cleanup.
    Use this when testing LocalFileBlobProvider or similar blob storage.
    
    Args:
        temp_dir: The base temporary directory (injected by pytest)
        
    Returns:
        Path: A subdirectory ready for blob storage testing
    """
    blob_path = temp_dir / "blob_storage"
    blob_path.mkdir(parents=True, exist_ok=True)
    return blob_path


@pytest.fixture
def character_storage_path(temp_dir: Path) -> Path:
    """
    Create a temporary directory for character storage tests.
    
    This fixture uses the temp_dir fixture, so it gets automatic cleanup.
    Use this when testing character CRUD operations that write to disk.
    
    Args:
        temp_dir: The base temporary directory (injected by pytest)
        
    Returns:
        Path: A subdirectory ready for character JSON file storage
    """
    char_path = temp_dir / "characters"
    char_path.mkdir(parents=True, exist_ok=True)
    return char_path
