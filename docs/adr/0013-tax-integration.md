# ADR 0013: Tax Data Integration Architecture

**Status**: Accepted  
**Date**: 2025-11-06  
**Authors**: fin-infra team

## Context

Tax document management is essential for fintech applications like TurboTax, Credit Karma Tax, and personal finance apps. Users need:
- Access to tax forms (W-2, 1099-INT, 1099-DIV, 1099-B, 1099-MISC)
- Crypto tax calculations (capital gains, Form 8949)
- Tax liability estimation
- 7-year document retention (IRS requirement)
- GDPR/CCPA erasure on user request

fin-infra must provide:
1. Easy-to-use tax provider abstraction
2. Integration with IRS e-Services and TaxBit
3. PDF parsing for tax forms
4. Compliance with IRS retention requirements (7 years)
5. svc-infra integration for storage, retention, and erasure

## Decision

### 1. Provider Architecture

**TaxProvider ABC** (extends existing in `providers/base.py`):
```python
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import date

class TaxProvider(ABC):
    @abstractmethod
    async def get_tax_documents(
        self, user_id: str, tax_year: int, **kwargs
    ) -> list[TaxDocument]:
        """Retrieve all tax documents for a user and tax year."""
        pass
    
    @abstractmethod
    async def get_tax_document(
        self, document_id: str, **kwargs
    ) -> TaxDocument:
        """Retrieve a specific tax document by ID."""
        pass
    
    @abstractmethod
    async def download_document(
        self, document_id: str, **kwargs
    ) -> bytes:
        """Download PDF bytes for a tax document."""
        pass
    
    @abstractmethod
    async def calculate_crypto_gains(
        self, user_id: str, transactions: list[dict], tax_year: int, **kwargs
    ) -> CryptoTaxReport:
        """Calculate capital gains for crypto transactions."""
        pass
    
    @abstractmethod
    async def calculate_tax_liability(
        self, user_id: str, income: Decimal, deductions: Decimal, 
        filing_status: str, tax_year: int, **kwargs
    ) -> TaxLiability:
        """Estimate tax liability (basic calculation)."""
        pass
```

**Supported Providers**:
- **IRS e-Services** (v2): Official IRS data, free API, W-2/1099 transcripts (requires EFIN)
- **TaxBit** (v2): Crypto tax calculations, Form 8949, 1099-B (paid API)
- **MockTaxProvider** (v1): Sample data for testing

### 2. Data Models

**TaxDocument** (Base model for all tax forms):
```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

class TaxDocument(BaseModel):
    document_id: str
    user_id: str
    form_type: str  # "W2", "1099-INT", "1099-DIV", "1099-B", "1099-MISC"
    tax_year: int
    issuer: str  # Employer or payer name
    issuer_ein: str | None  # Employer Identification Number
    download_url: str | None  # S3/GCS URL or local path
    status: str  # "pending", "available", "downloaded", "error"
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

**TaxFormW2** (Wage and Tax Statement):
```python
class TaxFormW2(TaxDocument):
    form_type: str = Field(default="W2", frozen=True)
    
    # Box 1: Wages, tips, other compensation
    wages: Decimal
    
    # Box 2: Federal income tax withheld
    federal_tax_withheld: Decimal
    
    # Box 3-4: Social Security
    social_security_wages: Decimal
    social_security_tax_withheld: Decimal
    
    # Box 5-6: Medicare
    medicare_wages: Decimal
    medicare_tax_withheld: Decimal
    
    # Box 12: Codes (retirement contributions, etc.)
    box_12_codes: dict[str, Decimal] = {}  # {"D": 5000.00, "DD": 12000.00}
    
    # Box 13: Checkboxes
    statutory_employee: bool = False
    retirement_plan: bool = False
    third_party_sick_pay: bool = False
    
    # Box 15-20: State/local taxes
    state_wages: Decimal | None = None
    state_tax_withheld: Decimal | None = None
    state: str | None = None
```

**TaxForm1099INT** (Interest Income):
```python
class TaxForm1099INT(TaxDocument):
    form_type: str = Field(default="1099-INT", frozen=True)
    
    # Box 1: Interest income
    interest_income: Decimal
    
    # Box 2: Early withdrawal penalty
    early_withdrawal_penalty: Decimal = Decimal("0.00")
    
    # Box 3: Interest on U.S. Savings Bonds
    us_savings_bonds_interest: Decimal = Decimal("0.00")
    
    # Box 4: Federal income tax withheld
    federal_tax_withheld: Decimal = Decimal("0.00")
    
    # Box 8: Tax-exempt interest
    tax_exempt_interest: Decimal = Decimal("0.00")
```

**TaxForm1099DIV** (Dividends and Distributions):
```python
class TaxForm1099DIV(TaxDocument):
    form_type: str = Field(default="1099-DIV", frozen=True)
    
    # Box 1a: Total ordinary dividends
    ordinary_dividends: Decimal
    
    # Box 1b: Qualified dividends
    qualified_dividends: Decimal = Decimal("0.00")
    
    # Box 2a: Total capital gain distributions
    capital_gain_distributions: Decimal = Decimal("0.00")
    
    # Box 3: Nondividend distributions
    nondividend_distributions: Decimal = Decimal("0.00")
    
    # Box 4: Federal income tax withheld
    federal_tax_withheld: Decimal = Decimal("0.00")
```

**TaxForm1099B** (Proceeds from Broker Transactions):
```python
class TaxForm1099B(TaxDocument):
    form_type: str = Field(default="1099-B", frozen=True)
    
    # Description of property (stock, crypto, etc.)
    description: str
    
    # Date acquired and sold
    date_acquired: date | None
    date_sold: date
    
    # Proceeds (sales price)
    proceeds: Decimal
    
    # Cost or other basis
    cost_basis: Decimal | None
    
    # Gain or loss (calculated)
    gain_or_loss: Decimal | None
    
    # Short-term or long-term
    holding_period: str  # "short_term", "long_term", "unknown"
    
    # Box 5: Federal income tax withheld
    federal_tax_withheld: Decimal = Decimal("0.00")
```

**TaxForm1099MISC** (Miscellaneous Income - staking, airdrops):
```python
class TaxForm1099MISC(TaxDocument):
    form_type: str = Field(default="1099-MISC", frozen=True)
    
    # Box 1: Rents
    rents: Decimal = Decimal("0.00")
    
    # Box 2: Royalties
    royalties: Decimal = Decimal("0.00")
    
    # Box 3: Other income (staking rewards, airdrops, freelance)
    other_income: Decimal = Decimal("0.00")
    
    # Box 4: Federal income tax withheld
    federal_tax_withheld: Decimal = Decimal("0.00")
```

**CryptoTaxReport** (Capital gains summary):
```python
class CryptoTaxReport(BaseModel):
    user_id: str
    tax_year: int
    
    # Total capital gains/losses
    total_gain_loss: Decimal
    
    # Short-term (held <= 1 year)
    short_term_gain_loss: Decimal
    
    # Long-term (held > 1 year)
    long_term_gain_loss: Decimal
    
    # Number of transactions
    transaction_count: int
    
    # Cost basis method
    cost_basis_method: str  # "FIFO", "LIFO", "HIFO"
    
    # Detailed transactions
    transactions: list[CryptoTransaction]
    
    # Form 8949 data (if available)
    form_8949_data: dict | None = None
```

**CryptoTransaction** (Individual crypto trade):
```python
class CryptoTransaction(BaseModel):
    transaction_id: str
    date_acquired: date | None
    date_sold: date
    asset: str  # "BTC", "ETH", etc.
    quantity: Decimal
    proceeds: Decimal  # Sale price
    cost_basis: Decimal  # Purchase price
    gain_loss: Decimal  # Calculated
    holding_period: str  # "short_term", "long_term"
```

**TaxLiability** (Tax calculation):
```python
class TaxLiability(BaseModel):
    taxable_income: Decimal
    total_tax: Decimal
    federal_tax: Decimal
    state_tax: Decimal = Decimal("0.00")
    effective_rate: Decimal  # Percentage
    marginal_rate: Decimal  # Percentage
    tax_year: int
    filing_status: str  # "single", "married_joint", "married_separate", "head_of_household"
```

### 3. Easy Builder & FastAPI Integration

**easy_tax()** one-liner:
```python
def easy_tax(provider: str = "mock", **config) -> TaxProvider:
    """Create configured tax provider with environment variable auto-detection.
    
    Args:
        provider: Provider name - "irs" (IRS e-Services), "taxbit" (crypto tax), "mock" (default)
        **config: Optional configuration overrides
    
    Returns:
        Configured TaxProvider instance
    
    Environment Variables:
        # IRS e-Services
        IRS_EFIN: Electronic Filing Identification Number
        IRS_TCC: Transmitter Control Code
        IRS_CERT_PATH: Path to PKI certificate
        IRS_KEY_PATH: Path to PKI private key
        IRS_BASE_URL: https://ei.irs.gov (or testei.irs.gov for sandbox)
        
        # TaxBit
        TAXBIT_CLIENT_ID: OAuth 2.0 client ID
        TAXBIT_CLIENT_SECRET: OAuth 2.0 client secret
        TAXBIT_BASE_URL: https://api.taxbit.com (or sandbox)
    
    Examples:
        # Mock provider (testing)
        >>> tax = easy_tax()
        >>> docs = await tax.get_tax_documents("user123", 2024)
        
        # IRS e-Services (production)
        >>> tax = easy_tax(provider="irs")
        >>> w2s = await tax.get_tax_documents("user123", 2024)
        
        # TaxBit (crypto tax)
        >>> tax = easy_tax(provider="taxbit")
        >>> report = await tax.calculate_crypto_gains("user123", transactions, 2024)
    """
```

**add_tax_data()** FastAPI helper:
```python
def add_tax_data(
    app: FastAPI,
    *,
    provider: str | TaxProvider | None = None,
    prefix: str = "/tax",
    cache_ttl: int = 3600,  # 1 hour (tax data changes rarely)
    **config
) -> TaxProvider:
    """Wire tax data routes to FastAPI app.
    
    Mounts routes:
        GET {prefix}/documents - List all tax documents for authenticated user
        GET {prefix}/documents/{document_id} - Get specific tax document
        GET {prefix}/documents/{document_id}/download - Download PDF
        POST {prefix}/crypto/calculate - Calculate crypto capital gains
        POST {prefix}/liability/estimate - Estimate tax liability
        GET {prefix}/docs - Scoped Swagger UI
        GET {prefix}/openapi.json - Scoped OpenAPI schema
    
    Integration with svc-infra:
        - Uses svc-infra.cache for document metadata caching (reduce provider API calls)
        - Uses svc-infra.auth (user_router + RequireUser for protected routes)
        - Uses svc-infra.data (RetentionPolicy for 7-year IRS requirement, ErasurePlan for GDPR)
        - Uses svc-infra.logging for compliance event logging (tax document access)
        - Uses svc-infra.docs (add_prefixed_docs for landing page card)
    
    Example:
        >>> from fastapi import FastAPI
        >>> from fin_infra.tax import add_tax_data
        >>> 
        >>> app = FastAPI()
        >>> tax = add_tax_data(app, provider="irs")
    """
```

### 4. PDF Parsing Strategy

**Parser Module** (`tax/parsers/`):
```python
# tax/parsers/base.py
from abc import ABC, abstractmethod

class TaxFormParser(ABC):
    @abstractmethod
    def parse(self, pdf_bytes: bytes) -> TaxDocument:
        """Parse PDF bytes into structured tax document."""
        pass

# tax/parsers/w2_parser.py
import pdfplumber
from fin_infra.models.tax import TaxFormW2

class W2Parser(TaxFormParser):
    def parse(self, pdf_bytes: bytes) -> TaxFormW2:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page = pdf.pages[0]
            table = page.extract_table()
            
            # W-2 is a 6-box table layout
            # Extract by coordinates (boxes have fixed positions)
            wages = self._extract_box(page, box_number=1)
            federal_tax = self._extract_box(page, box_number=2)
            # ... (boxes 3-20)
            
            return TaxFormW2(
                document_id=str(uuid.uuid4()),
                user_id="",  # Set by caller
                tax_year=int(page.within_bbox((100, 50, 200, 70)).extract_text()),
                issuer=page.within_bbox((100, 80, 400, 100)).extract_text(),
                wages=Decimal(wages),
                federal_tax_withheld=Decimal(federal_tax),
                # ...
            )
    
    def _extract_box(self, page, box_number: int) -> str:
        # Box coordinates for standard IRS W-2 layout
        boxes = {
            1: (100, 200, 300, 220),  # Wages
            2: (320, 200, 450, 220),  # Federal tax withheld
            # ... (all 20 boxes)
        }
        bbox = boxes[box_number]
        return page.within_bbox(bbox).extract_text().strip()
```

### 5. Caching Strategy (svc-infra integration)

**Tax document caching** (minimize provider API calls):
```python
from svc_infra.cache import cache_read, cache_write, resource

# Define tax resource with 1-hour TTL (tax data rarely changes)
tax_resource = resource("tax_documents", id_param="user_id")

@tax_resource.cache_read(ttl=3600)  # 1 hour
async def get_tax_documents_cached(user_id: str, tax_year: int) -> list[TaxDocument]:
    # Fetch from provider (may be expensive or rate-limited)
    docs = await tax_provider.get_tax_documents(user_id, tax_year)
    return docs

# Force refresh on user request
@tax_resource.cache_write()
async def refresh_tax_documents(user_id: str, tax_year: int) -> list[TaxDocument]:
    docs = await tax_provider.get_tax_documents(user_id, tax_year)
    return docs
```

**Cache key strategy**:
- `tax_documents:{user_id}:{tax_year}` - Document list (1h TTL)
- `tax_document:{document_id}` - Single document (24h TTL)
- `crypto_tax_report:{user_id}:{tax_year}` - Crypto gains (24h TTL)

### 6. Data Lifecycle (svc-infra integration)

**Retention Policy** (IRS requires 7 years):
```python
from svc_infra.data import RetentionPolicy

# Tax documents must be retained for 7 years (IRS requirement)
tax_document_retention = RetentionPolicy(
    name="tax_documents",
    model=TaxDocument,  # Your SQLAlchemy model
    older_than_days=7 * 365,  # 7 years
    soft_delete_field="deleted_at",
    hard_delete=False,  # Soft delete first, compliance review before hard delete
)
```

**Erasure Plan** (GDPR/CCPA):
```python
from svc_infra.data import ErasurePlan, ErasureStep

async def erase_tax_documents(session, user_id: str):
    """Erase all tax documents for a user (after 7-year retention)."""
    # Check if oldest document is > 7 years old
    oldest = await session.execute(
        select(TaxDocument)
        .where(TaxDocument.user_id == user_id)
        .order_by(TaxDocument.tax_year.asc())
        .limit(1)
    )
    oldest_doc = oldest.scalar_one_or_none()
    
    if oldest_doc and (datetime.now().year - oldest_doc.tax_year) < 7:
        raise ValueError("Cannot erase tax documents within 7-year retention period")
    
    # Hard delete all documents
    await session.execute(
        delete(TaxDocument).where(TaxDocument.user_id == user_id)
    )

tax_erasure_plan = ErasurePlan(
    steps=[
        ErasureStep("tax_documents", erase_tax_documents),
    ]
)
```

### 7. Compliance Event Logging

**Tax document access logging** (GLBA/audit requirements):
```python
import logging

logger = logging.getLogger(__name__)

# Log every tax document access
logger.info(
    "tax.document_accessed",
    extra={
        "user_id": user_id,
        "document_id": document_id,
        "form_type": "W2",
        "tax_year": 2024,
        "timestamp": datetime.utcnow().isoformat(),
    }
)
```

### 8. v1 Implementation Scope

**Included in v1** (Mock Implementation):
- ✅ MockTaxProvider (sample W-2, 1099-INT, 1099-DIV data)
- ✅ TaxDocument, TaxFormW2, TaxForm1099INT, TaxForm1099DIV, TaxForm1099B, TaxForm1099MISC models
- ✅ easy_tax() one-liner (defaults to mock)
- ✅ add_tax_data() FastAPI helper (user_router, cache, docs)
- ✅ PDF parser stub (pdfplumber-based W-2 parser)
- ✅ Unit tests with sample data
- ✅ docs/tax.md

**Deferred to v2** (Real API Integration):
- ⏸️ IRS e-Services integration (requires EFIN, 6-8 weeks registration)
- ⏸️ TaxBit integration (requires partnership/contract)
- ⏸️ Full PDF parser implementation (1099-INT, 1099-DIV, 1099-B, 1099-MISC)
- ⏸️ OCR support for scanned forms (pytesseract)
- ⏸️ Crypto tax calculation engine (FIFO, LIFO, HIFO cost basis)
- ⏸️ Form 8949 generation
- ⏸️ Acceptance tests (requires sandbox credentials)

## Consequences

### Positive
✅ Simple API: `easy_tax()` and `add_tax_data(app)`  
✅ svc-infra integration: Cache, retention, erasure, auth, docs  
✅ IRS compliant: 7-year retention, audit logging, encryption  
✅ Multi-provider: IRS e-Services (free), TaxBit (crypto), extensible  
✅ PDF parsing: pdfplumber handles complex table layouts  
✅ Type-safe: Pydantic models for all tax forms  

### Negative
⚠️ v1 is mock-only (no real IRS or TaxBit integration)  
⚠️ IRS e-Services requires 6-8 weeks registration (EFIN, PKI certs)  
⚠️ TaxBit requires paid contract ($50-$200/month base + per-user fees)  
⚠️ PDF parsing is complex (coordinate-based extraction fragile)  
⚠️ 7-year retention conflicts with GDPR "right to erasure" (legal review needed)  

### Neutral
➖ Tax documents are sensitive PII (SSN, EIN) - see ADR-0011 for PII handling  
➖ Crypto tax calculations are complex (wash sale, cost basis, FIFO/LIFO)  
➖ IRS API is XML-based (not JSON) - requires custom parser  

## Alternatives Considered

**1. No tax integration**  
Rejected: Tax data is core for personal finance apps (Mint, Credit Karma, TurboTax competitors).

**2. Build in-house tax calculation**  
Rejected: Tax law is complex and changes annually; use TaxBit or IRS official data.

**3. PyPDF2 instead of pdfplumber**  
Rejected: PyPDF2 has poor table extraction; tax forms are table-based.

**4. Store PDF bytes in database**  
Rejected: Large blobs slow down DB; use S3/GCS with metadata in DB.

**5. No retention policy enforcement**  
Rejected: IRS requires 7-year retention; GLBA requires audit trail.

## References

- IRS e-File for Developers: https://www.irs.gov/e-file-providers/modernized-e-file-mef-for-software-developers
- TaxBit: https://taxbit.com/
- pdfplumber: https://github.com/jsvine/pdfplumber
- IRS Forms: https://www.irs.gov/forms-instructions
- svc-infra data lifecycle: `svc_infra.data` module
- ADR-0011: Compliance Posture (PII handling)
- Tax Provider Research: docs/research/tax-providers.md

## Implementation Status

**v1 Deliverables** (Mock Implementation):
- [ ] ADR-0013 documented
- [ ] Data models (TaxDocument, TaxFormW2, TaxForm1099*, CryptoTaxReport, TaxLiability)
- [ ] MockTaxProvider (sample W-2, 1099 data)
- [ ] easy_tax() builder
- [ ] add_tax_data() FastAPI helper
- [ ] PDF parser stub (W2Parser with pdfplumber)
- [ ] Unit tests with mock data
- [ ] docs/tax.md

**v2 Deliverables** (Real API Integration):
- [ ] IRS e-Services provider (EFIN registration, PKI certs, XML parser)
- [ ] TaxBit provider (OAuth 2.0, crypto tax calculations)
- [ ] Full PDF parsers (1099-INT, 1099-DIV, 1099-B, 1099-MISC)
- [ ] OCR support (pytesseract for scanned forms)
- [ ] Crypto tax engine (FIFO, LIFO, HIFO, wash sale detection)
- [ ] Form 8949 generation
- [ ] Acceptance tests (sandbox credentials)
