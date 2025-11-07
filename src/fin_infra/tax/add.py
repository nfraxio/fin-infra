"""FastAPI integration for tax data.

add_tax_data() helper wires tax document routes to FastAPI app.
Uses svc-infra dual routers for consistent auth and OpenAPI docs.

Example:
    >>> from fastapi import FastAPI
    >>> from fin_infra.tax.add import add_tax_data
    >>> 
    >>> app = FastAPI()
    >>> tax_provider = add_tax_data(app)
    >>> 
    >>> # Routes mounted:
    >>> # GET /tax/documents?user_id=...&tax_year=2024
    >>> # GET /tax/documents/{document_id}
    >>> # POST /tax/crypto-gains
"""

from decimal import Decimal
from fastapi import FastAPI, Query, Body
from pydantic import BaseModel

from fin_infra.providers.base import TaxProvider


class CryptoGainsRequest(BaseModel):
    """Request body for crypto gains calculation."""
    user_id: str
    tax_year: int
    transactions: list[dict]  # List of crypto trades
    cost_basis_method: str = "FIFO"  # "FIFO", "LIFO", "HIFO"


class TaxLiabilityRequest(BaseModel):
    """Request body for tax liability estimation."""
    user_id: str
    tax_year: int
    income: Decimal
    deductions: Decimal
    filing_status: str  # "single", "married_joint", etc.
    state: str | None = None  # Two-letter state code (e.g., "CA")


def add_tax_data(
    app: FastAPI,
    provider: TaxProvider | str | None = None,
    prefix: str = "/tax",
) -> TaxProvider:
    """Wire tax data routes to FastAPI app.
    
    Mounts tax document retrieval and crypto tax calculation endpoints.
    Uses svc-infra user_router for protected routes (requires authentication).
    
    Args:
        app: FastAPI application instance
        provider: Tax provider instance or name (default: "mock")
        prefix: URL prefix for routes (default: "/tax")
    
    Returns:
        Configured TaxProvider instance
    
    Routes:
        GET {prefix}/documents: List all tax documents for user and year
        GET {prefix}/documents/{document_id}: Get specific tax document
        POST {prefix}/crypto-gains: Calculate crypto capital gains
        POST {prefix}/tax-liability: Estimate tax liability
    
    Example:
        >>> from fastapi import FastAPI
        >>> from fin_infra.tax.add import add_tax_data
        >>> 
        >>> app = FastAPI()
        >>> tax = add_tax_data(app, provider="mock", prefix="/tax")
        >>> 
        >>> # Now routes are available:
        >>> # GET /tax/documents?user_id=user123&tax_year=2024
        >>> # GET /tax/documents/w2_2024_user123
        >>> # POST /tax/crypto-gains
        >>> # POST /tax/tax-liability
    """
    # Import svc-infra dual router
    try:
        from svc_infra.api.fastapi.dual.protected import user_router
        from svc_infra.api.fastapi.docs.scoped import add_prefixed_docs
        use_dual_router = True
    except ImportError:
        # Fallback to generic APIRouter if svc-infra not available
        from fastapi import APIRouter
        user_router = APIRouter  # type: ignore
        use_dual_router = False
    
    # Initialize provider
    if provider is None:
        # Import here to avoid circular import
        from fin_infra.tax import easy_tax
        provider = easy_tax()
    elif isinstance(provider, str):
        from fin_infra.tax import easy_tax
        provider = easy_tax(provider=provider)
    
    # Create router with proper auth
    if use_dual_router:
        router = user_router(prefix=prefix, tags=["Tax Data"])
    else:
        router = APIRouter(prefix=prefix, tags=["Tax Data"])
    
    @router.get("/documents")
    async def get_tax_documents(
        user_id: str = Query(..., description="User identifier"),
        tax_year: int = Query(..., description="Tax year (e.g., 2024)")
    ):
        """Retrieve all tax documents for a user and tax year.
        
        Returns W-2, 1099-INT, 1099-DIV, 1099-B, 1099-MISC forms.
        
        Args:
            user_id: User identifier
            tax_year: Tax year (e.g., 2024)
        
        Returns:
            List of tax documents
        
        Example:
            GET /tax/documents?user_id=user123&tax_year=2024
            
            Response:
            [
              {
                "document_id": "w2_2024_user123",
                "user_id": "user123",
                "form_type": "W2",
                "tax_year": 2024,
                "issuer": "Acme Corporation",
                "wages": "75000.00",
                "federal_tax_withheld": "12000.00",
                ...
              },
              ...
            ]
        """
        return await provider.get_tax_documents(user_id, tax_year)
    
    @router.get("/documents/{document_id}")
    async def get_tax_document(document_id: str):
        """Retrieve a specific tax document by ID.
        
        Args:
            document_id: Document identifier (e.g., "w2_2024_user123")
        
        Returns:
            Tax document
        
        Example:
            GET /tax/documents/w2_2024_user123
            
            Response:
            {
              "document_id": "w2_2024_user123",
              "form_type": "W2",
              "wages": "75000.00",
              ...
            }
        """
        return await provider.get_tax_document(document_id)
    
    @router.post("/crypto-gains")
    async def calculate_crypto_gains(request: CryptoGainsRequest = Body(...)):
        """Calculate cryptocurrency capital gains/losses.
        
        Supports FIFO, LIFO, HIFO cost basis methods.
        Generates Form 8949 data and capital gains summary.
        
        Args:
            request: Crypto gains request with transactions
        
        Returns:
            CryptoTaxReport with gains/losses breakdown
        
        Example:
            POST /tax/crypto-gains
            {
              "user_id": "user123",
              "tax_year": 2024,
              "transactions": [
                {
                  "symbol": "BTC",
                  "type": "sell",
                  "date": "2024-06-20",
                  "quantity": 0.5,
                  "price": 60000.00,
                  "cost_basis": 40000.00
                }
              ],
              "cost_basis_method": "FIFO"
            }
            
            Response:
            {
              "user_id": "user123",
              "tax_year": 2024,
              "total_gain_loss": "10000.00",
              "short_term_gain_loss": "0.00",
              "long_term_gain_loss": "10000.00",
              "transaction_count": 1,
              "cost_basis_method": "FIFO",
              "transactions": [...]
            }
        """
        return await provider.calculate_crypto_gains(
            user_id=request.user_id,
            transactions=request.transactions,
            tax_year=request.tax_year,
            cost_basis_method=request.cost_basis_method
        )
    
    @router.post("/tax-liability")
    async def calculate_tax_liability(request: TaxLiabilityRequest = Body(...)):
        """Estimate tax liability (basic calculation).
        
        NOT a substitute for professional tax advice.
        Uses simplified tax brackets (not actual IRS tables).
        
        Args:
            request: Tax liability request with income and deductions
        
        Returns:
            TaxLiability estimate
        
        Example:
            POST /tax/tax-liability
            {
              "user_id": "user123",
              "tax_year": 2024,
              "income": "100000.00",
              "deductions": "14600.00",
              "filing_status": "single",
              "state": "CA"
            }
            
            Response:
            {
              "user_id": "user123",
              "tax_year": 2024,
              "filing_status": "single",
              "gross_income": "100000.00",
              "deductions": "14600.00",
              "taxable_income": "85400.00",
              "federal_tax": "12810.00",
              "state_tax": "4270.00",
              "total_tax": "17080.00",
              "effective_tax_rate": "17.08"
            }
        """
        return await provider.calculate_tax_liability(
            user_id=request.user_id,
            income=request.income,
            deductions=request.deductions,
            filing_status=request.filing_status,
            tax_year=request.tax_year,
            state=request.state
        )
    
    # Mount router
    app.include_router(router, include_in_schema=True)
    
    # Add scoped docs (if svc-infra available)
    if use_dual_router:
        add_prefixed_docs(
            app,
            prefix=prefix,
            title="Tax Data",
            auto_exclude_from_root=True,
            visible_envs=None,  # Show in all environments
        )
    
    # Store provider on app state
    app.state.tax_provider = provider
    
    return provider


__all__ = ["add_tax_data", "CryptoGainsRequest", "TaxLiabilityRequest"]
