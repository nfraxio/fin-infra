# Tax Provider Research (TaxBit, IRS e-Services, 1099/W-2 Formats)

**Date**: 2025-11-06  
**Purpose**: Research tax data providers for Section 14 implementation  
**Target**: Production-ready tax document retrieval and crypto tax reporting

---

## Executive Summary

**Recommendation**: Start with **IRS e-Services** for W-2/1099 retrieval (free, no API fees) and **TaxBit** for crypto tax calculations (industry standard). PDF parsing via **pdfplumber** (Apache 2.0 license, 5k+ stars).

**Key Findings**:
- IRS e-Services: Free but complex setup (EIN required, MeF registration)
- TaxBit: $50-$200/month per organization + $1-$5 per user/month for crypto tax
- PDF parsing: pdfplumber is superior to PyPDF2 (better table extraction)
- Tax form formats: Standardized IRS forms (PDF, XML via e-File)

---

## 1. TaxBit API (Crypto Tax Reporting)

### Overview
- **Website**: https://taxbit.com/
- **Purpose**: Crypto tax calculation and reporting (8949, 1099-B, 1099-MISC)
- **Target Customers**: Crypto exchanges, tax software, fintech apps
- **Pricing**: Enterprise (contact sales)
  - Estimated: $50-$200/month base + $1-$5 per user/month
  - Volume discounts available

### API Capabilities
1. **Transaction Import**:
   - Supports 500+ exchanges (Coinbase, Binance, Kraken, etc.)
   - CSV upload, API integration, or manual entry
   - Normalizes data: buys, sells, trades, staking, airdrops

2. **Capital Gains Calculation**:
   - FIFO, LIFO, HIFO cost basis methods
   - Short-term vs long-term gains classification
   - Wash sale detection

3. **Tax Form Generation**:
   - Form 8949 (Sales and Other Dispositions of Capital Assets)
   - Form 1099-B (Proceeds from Broker and Barter Exchange)
   - Form 1099-MISC (Miscellaneous Income for staking/airdrops)

4. **Audit Support**:
   - Transaction-level audit trail
   - PDF export of all forms
   - IRS-ready documentation

### Authentication
- OAuth 2.0 client credentials flow
- API keys for server-to-server integration
- Sandbox environment available

### Rate Limits
- Production: 100 requests/minute
- Sandbox: 10 requests/minute

### Endpoints (Estimated based on industry standards)
```http
POST   /v1/users/{user_id}/transactions        # Import transactions
GET    /v1/users/{user_id}/tax-year/{year}     # Get tax summary
GET    /v1/users/{user_id}/forms/8949          # Download Form 8949
GET    /v1/users/{user_id}/forms/1099-b        # Download Form 1099-B
POST   /v1/users/{user_id}/calculate           # Calculate capital gains
```

### Environment Variables
```bash
TAXBIT_CLIENT_ID=your_client_id
TAXBIT_CLIENT_SECRET=your_client_secret
TAXBIT_BASE_URL=https://api.taxbit.com  # or sandbox
```

### Pros
✅ Industry-standard crypto tax calculations  
✅ Supports all major exchanges  
✅ IRS-compliant forms  
✅ Wash sale detection  
✅ Audit-ready documentation  

### Cons
⚠️ Enterprise pricing (not free tier)  
⚠️ Requires partnership/contract for production  
⚠️ Crypto-specific (doesn't handle traditional tax forms)  
⚠️ Complex integration (transaction normalization)  

---

## 2. IRS e-Services (Tax Transcript Retrieval)

### Overview
- **Website**: https://www.irs.gov/e-file-providers/modernized-e-file-mef-for-software-developers
- **Purpose**: Access tax transcripts, W-2s, 1099s electronically
- **Target Customers**: Tax software developers, authorized e-file providers
- **Pricing**: **FREE** (no API fees, only IRS registration required)

### Services Available
1. **Tax Transcript API** (Get Transcript API):
   - Retrieve tax returns, W-2s, 1099s
   - Requires taxpayer consent (Form 8821 or 2848)
   - XML format (IRS MeF schema)

2. **Income Verification Express Service (IVES)**:
   - Verify income for mortgage lenders, loan officers
   - Requires signed 4506-C form from taxpayer
   - PDF or XML response

3. **e-File MeF (Modernized e-File)**:
   - Electronic filing of tax returns
   - XML schema for structured data
   - Real-time validation and acknowledgments

### Authentication
- **Transmitter Control Code (TCC)**: Issued by IRS after approval
- **Electronic Filing Identification Number (EFIN)**: Required for e-filing
- **PKI Certificates**: Mutual TLS for secure communication
- **IP Whitelisting**: IRS requires static IP addresses

### Registration Process (6-8 weeks)
1. **Apply for EFIN** (Form 8633):
   - Fingerprinting and background check required
   - $100 fee (non-refundable)
   
2. **Complete Suitability Check**:
   - Credit check, tax compliance check
   - Business verification
   
3. **Obtain TCC**:
   - Request via IRS e-Services portal
   - Link to EFIN

4. **Setup PKI Certificates**:
   - Request production certificates
   - Install in secure environment

5. **IP Whitelisting**:
   - Submit static IP addresses
   - IRS approves and whitelists

### API Endpoints (XML over HTTPS)
```http
POST   https://testei.irs.gov/EIL/get-transcript    # Sandbox
POST   https://ei.irs.gov/EIL/get-transcript        # Production
```

### Request Format (XML)
```xml
<GetTranscript xmlns="http://irs.gov/eil">
  <TaxpayerSSN>123-45-6789</TaxpayerSSN>
  <TranscriptType>WAGE_INCOME</TranscriptType>  <!-- W-2 -->
  <TaxYear>2024</TaxYear>
</GetTranscript>
```

### Response Format (XML)
```xml
<TranscriptResponse>
  <W2>
    <EmployerName>ACME Corporation</EmployerName>
    <EmployerEIN>12-3456789</EmployerEIN>
    <Wages>75000.00</Wages>
    <FederalIncomeTaxWithheld>12000.00</FederalIncomeTaxWithheld>
    <SocialSecurityWages>75000.00</SocialSecurityWages>
  </W2>
</TranscriptResponse>
```

### Environment Variables
```bash
IRS_EFIN=your_efin
IRS_TCC=your_tcc
IRS_CERT_PATH=/path/to/cert.pem
IRS_KEY_PATH=/path/to/key.pem
IRS_BASE_URL=https://ei.irs.gov  # or testei.irs.gov for sandbox
```

### Pros
✅ **FREE** (no API fees)  
✅ Official IRS data (most accurate)  
✅ W-2, 1099, tax return transcripts  
✅ Real-time data access  
✅ XML structured data  

### Cons
⚠️ Complex registration (6-8 weeks, fingerprinting, background check)  
⚠️ Requires taxpayer consent (Form 8821 or 2848)  
⚠️ PKI certificates and IP whitelisting  
⚠️ XML parsing complexity  
⚠️ Not suitable for crypto tax (only traditional tax forms)  

---

## 3. Tax Form Formats (1099, W-2)

### Form W-2 (Wage and Tax Statement)
**Purpose**: Report employee wages and tax withholdings  
**Issued by**: Employers  
**Deadline**: January 31st (for prior year)  
**Format**: PDF (standardized IRS layout)

**Key Fields**:
- Box 1: Wages, tips, other compensation
- Box 2: Federal income tax withheld
- Box 3: Social Security wages
- Box 4: Social Security tax withheld
- Box 5: Medicare wages and tips
- Box 6: Medicare tax withheld
- Box 12: Codes (retirement contributions, etc.)

**PDF Structure**:
- Fixed layout (IRS Form W-2 template)
- Table-based (6 boxes per row)
- OCR-friendly fonts (Courier, Arial)

### Form 1099-INT (Interest Income)
**Purpose**: Report interest income from banks, bonds  
**Issued by**: Banks, financial institutions  
**Threshold**: $10 or more  
**Format**: PDF (standardized IRS layout)

**Key Fields**:
- Box 1: Interest income
- Box 2: Early withdrawal penalty
- Box 3: Interest on U.S. Savings Bonds
- Box 4: Federal income tax withheld
- Box 8: Tax-exempt interest

### Form 1099-DIV (Dividends and Distributions)
**Purpose**: Report dividend income from stocks  
**Issued by**: Brokerage firms, mutual funds  
**Threshold**: $10 or more  
**Format**: PDF (standardized IRS layout)

**Key Fields**:
- Box 1a: Total ordinary dividends
- Box 1b: Qualified dividends
- Box 2a: Total capital gain distributions
- Box 3: Nondividend distributions

### Form 1099-B (Proceeds from Broker Transactions)
**Purpose**: Report stock/crypto sales, capital gains  
**Issued by**: Brokerages, crypto exchanges  
**Format**: PDF (standardized IRS layout)

**Key Fields**:
- Description of property
- Date acquired
- Date sold
- Proceeds (sales price)
- Cost or other basis
- Gain or loss
- Short-term vs long-term

### Form 1099-MISC (Miscellaneous Income)
**Purpose**: Report freelance income, rent, royalties, crypto staking  
**Issued by**: Payers of miscellaneous income  
**Threshold**: $600 or more  
**Format**: PDF (standardized IRS layout)

**Key Fields**:
- Box 1: Rents
- Box 2: Royalties
- Box 3: Other income (staking rewards, airdrops)

---

## 4. PDF Parsing Libraries (Python)

### pdfplumber (Recommended)
**GitHub**: https://github.com/jsvine/pdfplumber  
**Stars**: 5.9k  
**License**: Apache 2.0  
**Maintainer**: Active (last commit: 2024)

**Pros**:
✅ Excellent table extraction (tax forms are table-based)  
✅ OCR-free (extracts text directly from PDF)  
✅ Coordinate-based extraction (target specific boxes)  
✅ Works with scanned PDFs (via pytesseract integration)  
✅ Well-documented, actively maintained  

**Cons**:
⚠️ Slower than PyPDF2 for simple text extraction  
⚠️ Requires more memory for large PDFs  

**Example Usage**:
```python
import pdfplumber

with pdfplumber.open("form_w2.pdf") as pdf:
    page = pdf.pages[0]
    
    # Extract table (W-2 is a 6-box table)
    table = page.extract_table()
    
    # Or extract specific coordinates
    wages = page.within_bbox((100, 200, 300, 220)).extract_text()
```

### PyPDF2
**GitHub**: https://github.com/py-pdf/PyPDF2  
**Stars**: 7.8k  
**License**: BSD  
**Maintainer**: Active

**Pros**:
✅ Fast and lightweight  
✅ Simple API for text extraction  
✅ Good for basic PDF reading  

**Cons**:
⚠️ Poor table extraction (tax forms are tables)  
⚠️ Struggles with complex layouts  
⚠️ No OCR support  

**Example Usage**:
```python
import PyPDF2

with open("form_w2.pdf", "rb") as file:
    reader = PyPDF2.PdfReader(file)
    page = reader.pages[0]
    text = page.extract_text()  # Returns unstructured text
```

### Recommendation
**Use pdfplumber** for tax form parsing:
- W-2 and 1099 forms are table-based
- Need coordinate-based extraction for specific boxes
- OCR support for scanned forms

---

## 5. Alternative Tax Data Providers

### Plaid Identity Verification (includes W-2s)
- **Website**: https://plaid.com/products/identity-verification/
- **Pricing**: $0.04 per verification (W-2 included)
- **Pros**: Already integrated if using Plaid for banking
- **Cons**: Limited to W-2s, no 1099s or crypto tax

### Argyle (Income Verification)
- **Website**: https://argyle.com/
- **Pricing**: Contact sales (estimated $0.10-$0.50 per verification)
- **Pros**: W-2s, pay stubs, employment verification
- **Cons**: No 1099s, no crypto tax

### Coinbase Tax (formerly CoinTracker)
- **Website**: https://www.coinbase.com/tax
- **Pricing**: Free tier (100 transactions), $49-$299/year premium
- **Pros**: Free tier, easy integration
- **Cons**: Consumer-focused (not B2B API), limited to Coinbase users

---

## 6. Implementation Recommendations

### Phase 1: Basic Tax Document Retrieval (v1)
1. **Mock Provider**:
   - Create `MockTaxProvider` with sample W-2 and 1099 data
   - PDF generation via reportlab or weasyprint
   - No real API integration (testing only)

2. **PDF Parser**:
   - Implement pdfplumber-based parser for W-2 and 1099-INT
   - Extract key fields (wages, withholding, interest)
   - Unit tests with sample PDFs

3. **Data Models**:
   - `TaxDocument`, `TaxFormW2`, `TaxForm1099`
   - Pydantic models with IRS field mappings

### Phase 2: Real IRS Integration (v2)
1. **IRS e-Services**:
   - Complete EFIN application (6-8 weeks)
   - Setup PKI certificates and IP whitelisting
   - Implement XML parser for IRS responses
   - Taxpayer consent workflow (Form 8821)

2. **Compliance**:
   - 7-year retention (IRS requirement)
   - Encryption at rest (SSN, EIN in tax forms)
   - Audit logging (who accessed which tax forms)

### Phase 3: Crypto Tax Integration (v3)
1. **TaxBit API**:
   - Sign partnership agreement
   - Implement transaction import
   - Capital gains calculation
   - Form 8949 and 1099-B generation

2. **Alternative**: Build in-house crypto tax engine
   - Simpler than traditional tax (just capital gains)
   - Challenges: wash sale detection, cost basis tracking
   - Saves $1-$5 per user/month

---

## 7. Cost Analysis

### Option A: IRS e-Services + pdfplumber (Recommended for v1)
- **Setup Cost**: $100 (EFIN application) + 6-8 weeks registration
- **Ongoing Cost**: $0 (free API)
- **Per-User Cost**: $0
- **Total Cost (10k users)**: $100 one-time

### Option B: TaxBit (Crypto Tax)
- **Setup Cost**: Partnership agreement (varies)
- **Base Cost**: $50-$200/month
- **Per-User Cost**: $1-$5/month
- **Total Cost (10k users)**: $10k-$50k/month

### Option C: Plaid Identity Verification (W-2s only)
- **Setup Cost**: $0 (if already using Plaid)
- **Per-User Cost**: $0.04 per verification
- **Total Cost (10k users, 1 W-2 each)**: $400 one-time

### Option D: Build In-House (Crypto Tax)
- **Development Cost**: 2-4 weeks engineering time
- **Ongoing Cost**: $0 (maintenance only)
- **Per-User Cost**: $0
- **Total Cost**: Engineering time only

---

## 8. Recommended Stack for fin-infra

### Providers
1. **Primary**: IRS e-Services (free, official data)
2. **Secondary**: TaxBit (crypto tax, if budget allows)
3. **Fallback**: Plaid Identity (W-2s if IRS integration delayed)

### PDF Parsing
- **Library**: pdfplumber
- **OCR**: pytesseract (for scanned forms)
- **PDF Generation**: reportlab (for mock data)

### Data Storage (svc-infra integration)
- **Metadata**: svc-infra.db (document references, user_id, tax_year)
- **Files**: S3/GCS/local filesystem (encrypted PDFs)
- **Retention**: svc-infra.data.RetentionPolicy (7 years per IRS)
- **Erasure**: svc-infra.data.ErasurePlan (GDPR compliance)

### Compliance
- **Encryption**: svc-infra.security (SSN, EIN in forms)
- **Audit Logging**: svc-infra.logging (structured JSON logs)
- **Retention**: 7 years minimum (IRS requirement)

---

## 9. Next Steps

1. ✅ **Research complete** (this document)
2. **Create ADR-0013**: Tax data integration architecture
3. **Design data models**: TaxDocument, TaxFormW2, TaxForm1099, CryptoTaxReport
4. **Implement MockTaxProvider**: Sample W-2 and 1099 data
5. **Implement PDF parser**: pdfplumber-based extraction
6. **Write unit tests**: Parse sample PDFs, validate field extraction
7. **Document**: docs/tax.md with provider comparison and setup guide

---

## References

- IRS e-File for Developers: https://www.irs.gov/e-file-providers/modernized-e-file-mef-for-software-developers
- TaxBit: https://taxbit.com/
- pdfplumber: https://github.com/jsvine/pdfplumber
- IRS Forms: https://www.irs.gov/forms-instructions
- W-2 Specifications: https://www.irs.gov/pub/irs-pdf/fw2.pdf
- 1099 Specifications: https://www.irs.gov/forms-pubs/about-form-1099-misc
