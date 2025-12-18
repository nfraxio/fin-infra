"""Unit tests for financial document storage operations."""

import pytest
from svc_infra.storage.backends.memory import MemoryBackend

from fin_infra.documents.models import DocumentType
from fin_infra.documents.storage import (
    clear_storage,
    delete_document,
    download_document,
    get_document,
    list_documents,
    upload_document,
)


@pytest.fixture
def storage():
    """Create memory storage backend for testing."""
    return MemoryBackend()


@pytest.fixture(autouse=True)
def clear_metadata():
    """Clear document metadata before each test."""
    clear_storage()
    yield
    clear_storage()


@pytest.mark.asyncio
class TestUploadDocument:
    """Tests for upload_document function."""

    async def test_upload_basic_document(self, storage):
        """Test uploading a basic financial document."""
        file_content = b"Test document content"
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=file_content,
            document_type=DocumentType.TAX,
            filename="test.pdf",
            metadata={"year": 2024},
        )

        assert doc.id.startswith("doc_")
        assert doc.user_id == "user_123"
        assert doc.type == DocumentType.TAX
        assert doc.filename == "test.pdf"
        assert doc.file_size == len(file_content)
        assert doc.metadata["year"] == 2024
        assert doc.content_type == "application/pdf"
        assert doc.checksum is not None

    async def test_upload_without_metadata(self, storage):
        """Test uploading document without metadata."""
        doc = await upload_document(
            storage=storage,
            user_id="user_456",
            file=b"content",
            document_type=DocumentType.RECEIPT,
            filename="receipt.jpg",
        )

        # Metadata contains document_type (required for filtering)
        assert "document_type" in doc.metadata
        assert doc.metadata["document_type"] == "receipt"
        assert doc.content_type == "image/jpeg"

    async def test_upload_generates_unique_ids(self, storage):
        """Test that each upload generates a unique ID."""
        doc1 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content1",
            document_type=DocumentType.TAX,
            filename="doc1.pdf",
        )
        doc2 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content2",
            document_type=DocumentType.TAX,
            filename="doc2.pdf",
        )

        assert doc1.id != doc2.id

    async def test_upload_calculates_checksum(self, storage):
        """Test that checksum is calculated for uploaded files."""
        file_content = b"Test content for checksum"
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=file_content,
            document_type=DocumentType.STATEMENT,
            filename="statement.pdf",
        )

        assert doc.checksum is not None
        assert doc.checksum.startswith("sha256:")  # SHA-256 with prefix


@pytest.mark.asyncio
class TestGetDocument:
    """Tests for get_document function."""

    async def test_get_existing_document(self, storage):
        """Test getting an existing document."""
        uploaded = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
        )

        retrieved = get_document(uploaded.id)
        assert retrieved is not None
        assert retrieved.id == uploaded.id
        assert retrieved.filename == uploaded.filename

    async def test_get_nonexistent_document(self, storage):
        """Test getting a non-existent document returns None."""
        result = get_document("doc_nonexistent")
        assert result is None


@pytest.mark.asyncio
class TestDownloadDocument:
    """Tests for download_document function."""

    async def test_download_existing_document(self, storage):
        """Test downloading an existing document."""
        file_content = b"Test file content"
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=file_content,
            document_type=DocumentType.TAX,
            filename="test.pdf",
        )

        downloaded = await download_document(storage, doc.id)
        assert downloaded == file_content

    async def test_download_nonexistent_document(self, storage):
        """Test downloading non-existent document raises error."""
        with pytest.raises(ValueError, match="Document not found"):
            await download_document(storage, "doc_nonexistent")


@pytest.mark.asyncio
class TestDeleteDocument:
    """Tests for delete_document function."""

    async def test_delete_existing_document(self, storage):
        """Test deleting an existing document."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
        )

        await delete_document(storage, doc.id)

        # Verify document is deleted
        assert get_document(doc.id) is None

        # Verify file is deleted
        with pytest.raises(ValueError, match="Document not found"):
            await download_document(storage, doc.id)

    async def test_delete_nonexistent_document(self, storage):
        """Test deleting non-existent document returns False."""
        success = await delete_document(storage, "doc_nonexistent")
        assert success is False


@pytest.mark.asyncio
class TestListDocuments:
    """Tests for list_documents function."""

    async def test_list_all_user_documents(self, storage):
        """Test listing all documents for a user."""
        doc1 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content1",
            document_type=DocumentType.TAX,
            filename="tax.pdf",
        )
        doc2 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content2",
            document_type=DocumentType.RECEIPT,
            filename="receipt.pdf",
        )
        # Different user
        await upload_document(
            storage=storage,
            user_id="user_456",
            file=b"content3",
            document_type=DocumentType.TAX,
            filename="other.pdf",
        )

        docs = list_documents(user_id="user_123")
        assert len(docs) == 2
        assert doc1.id in [d.id for d in docs]
        assert doc2.id in [d.id for d in docs]

    async def test_list_documents_by_type(self, storage):
        """Test filtering documents by type."""
        doc1 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content1",
            document_type=DocumentType.TAX,
            filename="tax.pdf",
        )
        await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content2",
            document_type=DocumentType.RECEIPT,
            filename="receipt.pdf",
        )

        docs = list_documents(user_id="user_123", document_type=DocumentType.TAX)
        assert len(docs) == 1
        assert docs[0].id == doc1.id

    async def test_list_documents_by_year(self, storage):
        """Test filtering documents by year."""
        doc1 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content1",
            document_type=DocumentType.TAX,
            filename="tax_2024.pdf",
            tax_year=2024,
        )
        await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content2",
            document_type=DocumentType.TAX,
            filename="tax_2023.pdf",
            tax_year=2023,
        )

        docs = list_documents(user_id="user_123", tax_year=2024)
        assert len(docs) == 1
        assert docs[0].id == doc1.id

    async def test_list_documents_by_type_and_year(self, storage):
        """Test filtering by both type and year."""
        doc1 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content1",
            document_type=DocumentType.TAX,
            filename="tax_2024.pdf",
            tax_year=2024,
        )
        await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content2",
            document_type=DocumentType.TAX,
            filename="tax_2023.pdf",
            tax_year=2023,
        )
        await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content3",
            document_type=DocumentType.RECEIPT,
            filename="receipt_2024.pdf",
            tax_year=2024,
        )

        docs = list_documents(user_id="user_123", document_type=DocumentType.TAX, tax_year=2024)
        assert len(docs) == 1
        assert docs[0].id == doc1.id

    async def test_list_documents_sorted_by_date(self, storage):
        """Test that documents are sorted by upload date descending."""
        doc1 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content1",
            document_type=DocumentType.TAX,
            filename="first.pdf",
        )
        doc2 = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content2",
            document_type=DocumentType.TAX,
            filename="second.pdf",
        )

        docs = list_documents(user_id="user_123")
        # Most recent first
        assert docs[0].id == doc2.id
        assert docs[1].id == doc1.id

    async def test_list_documents_empty(self, storage):
        """Test listing documents for user with no documents."""
        docs = list_documents(user_id="user_empty")
        assert docs == []
