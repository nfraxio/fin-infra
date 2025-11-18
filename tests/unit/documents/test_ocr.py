"""Unit tests for OCR extraction."""

import pytest

from svc_infra.storage.backends.memory import MemoryBackend

from fin_infra.documents.models import DocumentType
from fin_infra.documents.ocr import clear_cache, extract_text
from fin_infra.documents.storage import clear_storage, upload_document


@pytest.fixture
def storage():
    """Create memory storage backend for testing."""
    return MemoryBackend()


@pytest.fixture(autouse=True)
def clean_caches():
    """Clear caches before and after each test."""
    clear_storage()
    clear_cache()
    yield
    clear_storage()
    clear_cache()


@pytest.mark.asyncio
class TestExtractText:
    """Tests for extract_text function."""

    async def test_extract_text_basic(self, storage):
        """Test basic text extraction."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"PDF content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
            tax_year=2024,
            form_type="W-2",
        )

        result = await extract_text(storage, doc.id, provider="tesseract")

        assert result.document_id == doc.id
        assert result.text is not None
        assert len(result.text) > 0
        assert result.confidence > 0
        assert result.provider == "tesseract"
        assert result.extraction_date is not None

    async def test_extract_text_w2_form(self, storage):
        """Test extracting text from W-2 tax form."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"W-2 content",
            document_type=DocumentType.TAX,
            filename="w2_2024.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={
                "employer": "Acme Corp",
                "wages": "85000",
                "federal_tax": "18700",
                "state_tax": "4250",
                "document_id": "doc_w2",
            },
        )

        result = await extract_text(storage, doc.id, provider="tesseract")

        assert "W-2" in result.text
        assert "Acme Corp" in result.text
        assert result.fields_extracted is not None
        assert "employer" in result.fields_extracted
        assert "wages" in result.fields_extracted

    async def test_extract_text_1099_form(self, storage):
        """Test extracting text from 1099 tax form."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"1099 content",
            document_type=DocumentType.TAX,
            filename="1099_2024.pdf",
            tax_year=2024,
            form_type="1099",
            metadata={
                "payer": "Client LLC",
                "income": "45000",
                "document_id": "doc_1099",
            },
        )

        result = await extract_text(storage, doc.id, provider="tesseract")

        assert "1099" in result.text
        assert "Client LLC" in result.text
        assert result.fields_extracted is not None

    async def test_extract_text_tesseract_provider(self, storage):
        """Test Tesseract provider has lower confidence."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={"document_id": "doc_tess"},
        )

        result = await extract_text(storage, doc.id, provider="tesseract")

        assert result.provider == "tesseract"
        # Tesseract should have lower confidence
        assert 0.80 <= result.confidence <= 0.90

    async def test_extract_text_textract_provider(self, storage):
        """Test AWS Textract provider has higher confidence."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={"document_id": "doc_textract"},
        )

        result = await extract_text(storage, doc.id, provider="textract")

        assert result.provider == "textract"
        # Textract should have higher confidence
        assert result.confidence >= 0.90

    async def test_extract_text_caching(self, storage):
        """Test that OCR results are cached."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={"document_id": "doc_cache"},
        )

        result1 = await extract_text(storage, doc.id, provider="tesseract")
        result2 = await extract_text(storage, doc.id, provider="tesseract")

        # Should be the same cached result
        assert result1.extraction_date == result2.extraction_date
        assert result1.text == result2.text

    async def test_extract_text_force_refresh(self, storage):
        """Test force refresh bypasses cache."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={"document_id": "doc_refresh"},
        )

        result1 = await extract_text(storage, doc.id, provider="tesseract")
        result2 = await extract_text(storage, doc.id, provider="tesseract", force_refresh=True)

        # Should have different extraction dates
        assert result1.extraction_date != result2.extraction_date

    async def test_extract_text_invalid_provider(self, storage):
        """Test invalid provider raises error."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
            metadata={"document_id": "doc_invalid"},
        )

        with pytest.raises(ValueError, match="Unknown OCR provider"):
            await extract_text(storage, doc.id, provider="invalid")

    async def test_extract_text_nonexistent_document(self, storage):
        """Test extracting from non-existent document raises error."""
        with pytest.raises(ValueError, match="Document not found"):
            await extract_text(storage, "doc_nonexistent")

    async def test_extract_text_generic_document(self, storage):
        """Test extracting text from generic document type."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"Generic content",
            document_type=DocumentType.RECEIPT,
            filename="receipt.pdf",
        )

        result = await extract_text(storage, doc.id, provider="tesseract")

        assert result.document_id == doc.id
        assert result.text is not None
        assert result.confidence > 0

    async def test_extract_text_fields_extracted(self, storage):
        """Test that structured fields are extracted from W-2."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"W-2 content",
            document_type=DocumentType.TAX,
            filename="w2.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={
                "employer": "Test Company",
                "wages": "100000",
                "federal_tax": "22000",
                "state_tax": "5000",
                "document_id": "doc_fields",
            },
        )

        result = await extract_text(storage, doc.id, provider="textract")

        # Should have extracted fields
        assert len(result.fields_extracted) > 0
        assert "employer" in result.fields_extracted
        assert result.fields_extracted["employer"] == "Test Company"
        assert "wages" in result.fields_extracted
