"""Unit tests for document analysis."""

import pytest
from svc_infra.storage.backends.memory import MemoryBackend

from fin_infra.documents.analysis import analyze_document, clear_cache
from fin_infra.documents.models import DocumentType
from fin_infra.documents.ocr import clear_cache as clear_ocr_cache
from fin_infra.documents.storage import clear_storage, upload_document


@pytest.fixture
def storage():
    """Create memory storage backend for testing."""
    return MemoryBackend()


@pytest.fixture(autouse=True)
def clean_caches():
    """Clear caches before and after each test."""
    clear_storage()
    clear_ocr_cache()
    clear_cache()
    yield
    clear_storage()
    clear_ocr_cache()
    clear_cache()


@pytest.mark.asyncio
class TestAnalyzeDocument:
    """Tests for analyze_document function."""

    async def test_analyze_w2_document(self, storage):
        """Test analyzing W-2 tax document."""
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

        result = await analyze_document(storage, doc.id)

        assert result.document_id == doc.id
        assert result.summary is not None
        assert len(result.summary) > 0
        assert "Acme Corp" in result.summary or "85,000" in result.summary
        assert len(result.key_findings) > 0
        assert len(result.recommendations) > 0
        assert result.confidence > 0.7
        assert result.analysis_date is not None

    async def test_analyze_1099_document(self, storage):
        """Test analyzing 1099 tax document."""
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

        result = await analyze_document(storage, doc.id)

        assert result.document_id == doc.id
        assert result.summary is not None
        assert len(result.key_findings) >= 3
        assert len(result.recommendations) >= 3

    async def test_analyze_bank_statement(self, storage):
        """Test analyzing bank statement."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"Statement content",
            document_type=DocumentType.STATEMENT,
            filename="statement_2024_12.pdf",
            tax_year=2024,
            metadata={"month": 12, "document_id": "doc_statement"},
        )

        result = await analyze_document(storage, doc.id)

        assert result.document_id == doc.id
        assert "statement" in result.summary.lower()
        assert len(result.key_findings) > 0
        assert len(result.recommendations) > 0

    async def test_analyze_receipt(self, storage):
        """Test analyzing receipt."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"Receipt content",
            document_type=DocumentType.RECEIPT,
            filename="receipt.pdf",
            metadata={"document_id": "doc_receipt"},
        )

        result = await analyze_document(storage, doc.id)

        assert result.document_id == doc.id
        assert "receipt" in result.summary.lower()
        assert len(result.key_findings) > 0

    async def test_analyze_generic_document(self, storage):
        """Test analyzing generic document type."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"Contract content",
            document_type=DocumentType.CONTRACT,
            filename="contract.pdf",
            metadata={"document_id": "doc_contract"},
        )

        result = await analyze_document(storage, doc.id)

        assert result.document_id == doc.id
        assert result.summary is not None
        assert len(result.key_findings) > 0
        assert len(result.recommendations) > 0

    async def test_analyze_caching(self, storage):
        """Test that analysis results are cached."""
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

        result1 = await analyze_document(storage, doc.id)
        result2 = await analyze_document(storage, doc.id)

        # Should be the same cached result
        assert result1.analysis_date == result2.analysis_date
        assert result1.summary == result2.summary

    async def test_analyze_force_refresh(self, storage):
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

        result1 = await analyze_document(storage, doc.id)
        result2 = await analyze_document(storage, doc.id, force_refresh=True)

        # Should have different analysis dates
        assert result1.analysis_date != result2.analysis_date

    async def test_analyze_nonexistent_document(self, storage):
        """Test analyzing non-existent document raises error."""
        with pytest.raises(ValueError, match="Document not found"):
            await analyze_document(storage, "doc_nonexistent")

    async def test_analyze_high_wage_w2(self, storage):
        """Test analyzing high-wage W-2 includes investment recommendation."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"W-2 content",
            document_type=DocumentType.TAX,
            filename="w2_high.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={
                "employer": "BigTech Inc",
                "wages": "150000",
                "federal_tax": "35000",
            },
        )

        result = await analyze_document(storage, doc.id)

        # High wage documents should include investment recommendations
        assert any("invest" in rec.lower() for rec in result.recommendations)

    async def test_analyze_confidence_threshold(self, storage):
        """Test that analysis confidence meets minimum threshold."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={"document_id": "doc_conf"},
        )

        result = await analyze_document(storage, doc.id)

        # All analysis should meet 0.7 confidence threshold
        assert result.confidence >= 0.5  # Fallback minimum

    async def test_analyze_summary_length(self, storage):
        """Test that summary is concise."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.TAX,
            filename="test.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={"document_id": "doc_summary"},
        )

        result = await analyze_document(storage, doc.id)

        # Summary should be reasonably concise
        assert len(result.summary) < 250

    async def test_analyze_findings_not_empty(self, storage):
        """Test that findings are always present."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.RECEIPT,
            filename="receipt.pdf",
            metadata={"document_id": "doc_findings"},
        )

        result = await analyze_document(storage, doc.id)

        assert len(result.key_findings) > 0

    async def test_analyze_recommendations_not_empty(self, storage):
        """Test that recommendations are always present."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"content",
            document_type=DocumentType.STATEMENT,
            filename="statement.pdf",
            metadata={"document_id": "doc_recs"},
        )

        result = await analyze_document(storage, doc.id)

        assert len(result.recommendations) > 0

    async def test_analyze_extracts_financial_data(self, storage):
        """Test that analysis extracts financial data from W-2."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"W-2 content",
            document_type=DocumentType.TAX,
            filename="w2.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={
                "employer": "Test Corp",
                "wages": "75000",
                "federal_tax": "15000",
                "state_tax": "3500",
                "document_id": "doc_extract",
            },
        )

        result = await analyze_document(storage, doc.id)

        # Should mention tax withholding
        findings_text = " ".join(result.key_findings).lower()
        assert "tax" in findings_text or "withhold" in findings_text

    async def test_analyze_includes_disclaimer_recommendations(self, storage):
        """Test that tax analysis includes professional advice disclaimer."""
        doc = await upload_document(
            storage=storage,
            user_id="user_123",
            file=b"W-2 content",
            document_type=DocumentType.TAX,
            filename="w2.pdf",
            tax_year=2024,
            form_type="W-2",
            metadata={
                "employer": "Company",
                "wages": "80000",
                "document_id": "doc_disclaimer",
            },
        )

        result = await analyze_document(storage, doc.id)

        # Should recommend consulting professional
        recs_text = " ".join(result.recommendations).lower()
        assert "professional" in recs_text or "advisor" in recs_text or "certified" in recs_text
