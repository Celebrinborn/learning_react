"""Tests for blob storage provider implementations."""
import pytest
from pathlib import Path

from providers.local_file_blob import LocalFileBlobProvider


class TestLocalFileBlobProvider:
    """Tests for the local file system blob storage provider."""

    @pytest.fixture
    def provider(self, blob_storage_path: Path) -> LocalFileBlobProvider:
        """Create a LocalFileBlobProvider instance for testing."""
        return LocalFileBlobProvider(blob_storage_path)

    @pytest.mark.asyncio
    async def test_write_and_read(self, provider: LocalFileBlobProvider):
        """Test writing and reading blob data."""
        test_data = b"Hello, World!"
        test_path = "test/file.txt"

        await provider.write(test_path, test_data)
        result = await provider.read(test_path)

        assert result == test_data

    @pytest.mark.asyncio
    async def test_read_nonexistent_file_raises_error(self, provider: LocalFileBlobProvider):
        """Test that reading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await provider.read("nonexistent/file.txt")

    @pytest.mark.asyncio
    async def test_write_creates_parent_directories(self, provider: LocalFileBlobProvider):
        """Test that writing creates parent directories automatically."""
        test_data = b"Test data"
        test_path = "deep/nested/directory/file.txt"

        await provider.write(test_path, test_data)
        result = await provider.read(test_path)

        assert result == test_data

    @pytest.mark.asyncio
    async def test_delete(self, provider: LocalFileBlobProvider):
        """Test deleting a blob."""
        test_data = b"To be deleted"
        test_path = "delete_me.txt"

        await provider.write(test_path, test_data)
        assert await provider.exists(test_path)

        await provider.delete(test_path)
        assert not await provider.exists(test_path)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_raises_error(self, provider: LocalFileBlobProvider):
        """Test that deleting a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await provider.delete("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_exists(self, provider: LocalFileBlobProvider):
        """Test checking if a blob exists."""
        test_path = "exists_test.txt"

        assert not await provider.exists(test_path)

        await provider.write(test_path, b"data")
        assert await provider.exists(test_path)

    @pytest.mark.asyncio
    async def test_list_empty(self, provider: LocalFileBlobProvider):
        """Test listing blobs in an empty storage."""
        result = await provider.list()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_multiple_files(self, provider: LocalFileBlobProvider):
        """Test listing multiple blobs."""
        files = ["file1.txt", "file2.txt", "subdir/file3.txt"]

        for file_path in files:
            await provider.write(file_path, b"data")

        result = await provider.list()
        assert sorted(result) == sorted(files)

    @pytest.mark.asyncio
    async def test_list_with_prefix(self, provider: LocalFileBlobProvider):
        """Test listing blobs with a prefix filter."""
        await provider.write("prefix/file1.txt", b"data")
        await provider.write("prefix/file2.txt", b"data")
        await provider.write("other/file3.txt", b"data")

        result = await provider.list("prefix")
        assert len(result) == 2
        assert all(path.startswith("prefix") for path in result)

    @pytest.mark.asyncio
    async def test_path_traversal_protection(self, provider: LocalFileBlobProvider):
        """Test that path traversal attempts are blocked."""
        with pytest.raises(ValueError):
            await provider.write("../../../etc/passwd", b"malicious")

        with pytest.raises(ValueError):
            await provider.read("../../sensitive_data.txt")

    @pytest.mark.asyncio
    async def test_get_url(self, provider: LocalFileBlobProvider):
        """Test getting a file:// URL for a blob."""
        test_path = "url_test.txt"
        await provider.write(test_path, b"data")

        url = provider.get_url(test_path)
        assert url.startswith("file://")
        assert "url_test.txt" in url

    @pytest.mark.asyncio
    async def test_write_overwrites_existing_file(self, provider: LocalFileBlobProvider):
        """Test that writing to an existing path overwrites the file."""
        test_path = "overwrite.txt"

        await provider.write(test_path, b"original")
        await provider.write(test_path, b"updated")

        result = await provider.read(test_path)
        assert result == b"updated"

    @pytest.mark.asyncio
    async def test_binary_data_integrity(self, provider: LocalFileBlobProvider):
        """Test that binary data is stored and retrieved correctly."""
        # Use various byte values including null bytes
        test_data = bytes(range(256))
        test_path = "binary_test.bin"

        await provider.write(test_path, test_data)
        result = await provider.read(test_path)

        assert result == test_data
        assert len(result) == 256
