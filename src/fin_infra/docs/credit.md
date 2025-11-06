# Credit Score Monitoring

**Provider**: Experian, Equifax (future), TransUnion (future)  
**Status**: ✅ v1 Complete (mock implementation)  
**Regulation**: FCRA (Fair Credit Reporting Act)

## Overview

Credit score monitoring enables fintech applications to:
- Retrieve user credit scores (FICO, VantageScore)
- Access full credit reports (accounts, inquiries, payment history)
- Subscribe to score change notifications
- Display credit insights (factors, utilization, etc.)

**Use cases**: Credit Karma, Credit Sesame, Mint, personal finance apps

## Quick Start

### Zero-Config Usage

```python
from fin_infra.credit import easy_credit

# Uses EXPERIAN_API_KEY from environment
credit = easy_credit()
score = credit.get_credit_score("user123")

print(f"Score: {score.score} ({score.score_model})")
print(f"Change: {score.change:+d} points")
```

### FastAPI Integration

```python
from fastapi import FastAPI
from fin_infra.credit.add import add_credit_monitoring

app = FastAPI()

# Wire credit routes (GET /credit/score, /credit/report, etc.)
credit = add_credit_monitoring(app, provider="experian")

# Routes available:
# GET /credit/score?user_id=user123
# GET /credit/report?user_id=user123
# POST /credit/subscribe?user_id=user123&webhook_url=...
```

### Full Credit Report

```python
from fin_infra.credit import easy_credit

credit = easy_credit()
report = credit.get_credit_report("user123")

print(f"Score: {report.score.score}")
print(f"Accounts: {len(report.accounts)}")
print(f"Inquiries: {len(report.inquiries)}")

# Access account details
for account in report.accounts:
    print(f"{account.creditor_name}: ${account.balance}")
```

## Data Models

### CreditScore

```python
from fin_infra.models.credit import CreditScore

score = CreditScore(
    user_id="user123",
    score=735,
    score_model="FICO 8",
    bureau="experian",
    score_date=date.today(),
    factors=[
        "Credit card utilization is high (35%)",
        "No recent late payments",
        "Average age of accounts is good (8 years)",
    ],
    change=15  # +15 points since last pull
)
```

**Fields**:
- `score` (int): Credit score 300-850
- `score_model` (str): "FICO 8", "VantageScore 3.0", etc.
- `bureau` (str): "experian", "equifax", "transunion"
- `factors` (list[str]): Factors affecting score
- `change` (int | None): Change since last pull

### CreditReport

```python
from fin_infra.models.credit import CreditReport

report = CreditReport(
    user_id="user123",
    bureau="experian",
    report_date=date.today(),
    score=score,
    accounts=[...],           # List of CreditAccount
    inquiries=[...],          # List of CreditInquiry
    public_records=[...],     # List of PublicRecord
    consumer_statements=[...] # Disputes, etc.
)
```

### CreditAccount (Tradeline)

```python
from fin_infra.models.credit import CreditAccount

account = CreditAccount(
    account_id="acc123",
    account_type="credit_card",  # or "mortgage", "auto_loan", "student_loan"
    creditor_name="Chase Bank",
    account_status="open",
    balance=Decimal("5000.00"),
    credit_limit=Decimal("10000.00"),
    payment_status="current",    # or "30_days_late", "60_days_late", etc.
    opened_date=date(2020, 1, 1),
    last_payment_date=date(2025, 1, 1),
)
```

### CreditInquiry (Hard/Soft Pulls)

```python
from fin_infra.models.credit import CreditInquiry

inquiry = CreditInquiry(
    inquiry_id="inq123",
    inquiry_type="hard",         # or "soft"
    inquirer_name="Chase Bank",
    inquiry_date=date(2025, 1, 1),
    purpose="credit_card_application"  # Optional
)
```

## Bureau Comparison

| Feature | Experian (v1) | Equifax (v2) | TransUnion (v2) |
|---------|---------------|--------------|-----------------|
| **Credit Scores** | ✅ FICO 8 | ⏸️ FICO 8, VantageScore | ⏸️ FICO 8, VantageScore |
| **Credit Reports** | ✅ Mock data | ⏸️ Full reports | ⏸️ Full reports |
| **Sandbox** | ✅ Free tier | ⏸️ Enterprise | ⏸️ Enterprise |
| **Webhooks** | ⏸️ v2 | ⏸️ v2 | ⏸️ v2 |
| **Cost** | ~$0.50-$2.00/pull | ~$0.50-$2.00/pull | ~$0.50-$2.00/pull |
| **API Docs** | [Experian Connect](https://developer.experian.com/) | [Equifax API](https://www.equifax.com/business/api/) | [TransUnion API](https://www.transunion.com/business/products-services/apis) |

**v1 Note**: v1 implements Experian with mock data only. Real API integration requires API key and is deferred to v2.

## Environment Variables

### Experian

```bash
# API credentials (get from https://developer.experian.com/)
EXPERIAN_API_KEY=your_api_key_here
EXPERIAN_CLIENT_ID=your_client_id_here  # If required
EXPERIAN_ENVIRONMENT=sandbox  # or "production"
```

## Integration with svc-infra

### Caching (Reduce Bureau Costs)

**Problem**: Bureau pulls cost ~$0.50-$2.00 each. Without caching, costs scale linearly with user requests.

**Solution**: Use `svc-infra.cache` with 24h TTL (industry standard for credit monitoring):

```python
from svc_infra.cache import cache_read, cache_write, resource
from fin_infra.credit import easy_credit

credit = easy_credit()

# Define credit resource with 24-hour TTL
credit_resource = resource("credit_score", id_param="user_id")

@credit_resource.cache_read(ttl=86400)  # 24 hours
async def get_credit_score_cached(user_id: str):
    # Fetch from bureau (expensive - ~$0.50-$2.00)
    score = credit.get_credit_score(user_id)
    return score

# Invalidate cache on user request or webhook notification
@credit_resource.cache_write()
async def refresh_credit_score(user_id: str):
    # Force fresh pull
    score = credit.get_credit_score(user_id)
    return score
```

**Cost savings**: With 24h caching, a user checking their score 10 times/day costs **1 pull/day** instead of **10 pulls/day** (90% savings).

## Cost Optimization (Caching Impact)

### Bureau API Costs

Credit bureau API pulls are expensive:
- **Experian**: $0.50 - $2.00 per credit score pull
- **Full credit reports**: $2.00 - $5.00 per pull
- **Typical fintech app**: 10+ user requests per day per active user

### Without Caching

**Example scenario** (1,000 active users):
- Users check score: **10 times/day average**
- Total pulls/day: **10,000 pulls**
- Cost/pull: **$1.00 (average)**
- **Daily cost**: **$10,000**
- **Monthly cost**: **$300,000**

### With 24-Hour Cache (Recommended)

**Same scenario with `cache_ttl=86400` (24 hours)**:
- Users check score: **10 times/day average**
- Bureau pulls: **1 pull/day per user** (cached 24h)
- Total pulls/day: **1,000 pulls**
- Cost/pull: **$1.00**
- **Daily cost**: **$1,000**
- **Monthly cost**: **$30,000**

**Savings**: **$270,000/month (90% reduction)** 🎉

### Cache TTL Comparison

| Cache TTL | Pulls/Day (1k users) | Cost/Month | Savings vs No Cache |
|-----------|---------------------|------------|---------------------|
| **No cache** | 10,000 | $300,000 | 0% |
| **1 hour** | 2,400 | $72,000 | 76% |
| **6 hours** | 1,600 | $48,000 | 84% |
| **12 hours** | 1,200 | $36,000 | 88% |
| **24 hours** ✅ | 1,000 | $30,000 | **90%** |
| **48 hours** | 800 | $24,000 | 92% |

**Industry standard**: 24-hour cache (balances cost savings with data freshness)

### Implementation in add_credit()

The `add_credit()` helper automatically uses 24-hour caching:

```python
from fastapi import FastAPI
from fin_infra.credit.add import add_credit
from svc_infra.cache import init_cache

app = FastAPI()

# Initialize cache backend (Redis recommended for production)
init_cache(url="redis://localhost:6379")

# Wire credit routes with 24h cache (default)
credit = add_credit(app, cache_ttl=86400)  # 86400 seconds = 24 hours

# Cost optimization:
# - First request: Hits bureau API ($1.00 cost)
# - Next 23 hours: Returns cached data ($0 cost)
# - After 24h: Cache expires, next request hits API again
```

### Custom Cache TTL

Adjust `cache_ttl` based on your use case:

```python
# More frequent updates (higher cost, fresher data)
credit = add_credit(app, cache_ttl=3600)  # 1 hour

# Less frequent updates (lower cost, stale data risk)
credit = add_credit(app, cache_ttl=172800)  # 48 hours

# No caching (not recommended - very expensive)
credit = add_credit(app, cache_ttl=0)  # Every request hits bureau API
```

**Recommendation**: Use 24-hour cache unless you have specific business requirements for fresher data.

### Cost savings**: With 24h caching, a user checking their score 10 times/day costs **1 pull/day** instead of **10 pulls/day** (90% savings).

### Webhooks (Score Change Notifications)

**v2 Integration** (not implemented in v1):

```python
from svc_infra.webhooks import add_webhooks, webhook_event
from fastapi import FastAPI

app = FastAPI()

# Wire webhooks
add_webhooks(app, events=["credit.score_changed"])

# Emit event when bureau notifies us of score change
await webhook_event(
    app,
    "credit.score_changed",
    {
        "user_id": "user123",
        "old_score": 720,
        "new_score": 735,
        "change": +15,
        "bureau": "experian"
    }
)
```

Users can subscribe to webhooks at `POST /credit/subscribe` endpoint.

### Compliance Event Logging (FCRA)

**FCRA requirement**: All credit report accesses must be logged with permissible purpose.

```python
from fin_infra.compliance import log_compliance_event

# Log every credit report access
log_compliance_event(
    app,
    "credit.report_accessed",
    {
        "user_id": user_id,
        "bureau": "experian",
        "purpose": "consumer_disclosure",  # FCRA permissible purpose
        "timestamp": datetime.utcnow().isoformat(),
    }
)
```

**Permissible purposes** (FCRA §604):
- Consumer disclosure (user requesting their own report)
- Credit transaction (loan application)
- Employment purposes (with user consent)
- Account review (existing creditor)
- Collection activity

**Important**: fin-infra does NOT enforce permissible purpose in v1. Production apps MUST implement consent workflows and purpose tracking.

## FCRA Compliance (§604 Permissible Purposes)

### Overview

The **Fair Credit Reporting Act (FCRA) §604** restricts who can access consumer credit reports and for what purposes. Violations can result in significant fines and legal liability.

**Key requirement**: Every credit report access must have a **permissible purpose** as defined by FCRA §604.

### Permissible Purposes (FCRA §604)

Credit reports may ONLY be accessed for the following purposes:

1. **Consumer Request (§604(a)(2))** ✅ **Most common for fintech apps**
   - User requests their own credit report
   - No additional authorization required beyond user consent
   - Example: Credit monitoring apps like Credit Karma

2. **Credit Transaction (§604(a)(3)(A))**
   - User initiates application for credit
   - Lender needs report to evaluate creditworthiness
   - Example: Mortgage application, credit card application

3. **Account Review (§604(a)(3)(C))**
   - Existing creditor reviewing account
   - Periodic review of consumer's creditworthiness
   - Example: Credit limit increase evaluation

4. **Employment Purposes (§604(b))**
   - Background checks for hiring
   - Requires written authorization from consumer
   - Strict consent requirements

5. **Collection Activity (§604(a)(3)(A))**
   - Collecting debt owed by consumer
   - Must have legitimate business relationship

6. **Court Order or Subpoena (§604(a)(1))**
   - Federal grand jury subpoena
   - Court order with connection to proceeding

**Important**: For fintech apps, **Consumer Request (§604(a)(2))** is typically the only applicable permissible purpose.

### Implementation Requirements

#### 1. User Consent Workflow

Users must explicitly consent to credit pulls:

```python
from fastapi import FastAPI, HTTPException
from fin_infra.credit.add import add_credit

app = FastAPI()
credit = add_credit(app)

# Example consent flow
@app.post("/credit/consent")
async def grant_credit_consent(user_id: str, consent: bool):
    """User grants consent for credit monitoring."""
    if not consent:
        raise HTTPException(400, "User must consent to credit monitoring")
    
    # Store consent in database
    await db.save_consent(
        user_id=user_id,
        purpose="consumer_disclosure",  # FCRA §604(a)(2)
        granted_at=datetime.utcnow(),
        ip_address=request.client.host,
    )
    
    return {"ok": True}
```

#### 2. Permissible Purpose Logging

**Every credit access MUST be logged** with permissible purpose:

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/credit/score")
async def get_credit_score(user_id: str):
    # FCRA compliance logging
    logger.info(
        "credit.score_accessed",
        extra={
            "user_id": user_id,
            "bureau": "experian",
            "permissible_purpose": "consumer_disclosure",  # FCRA §604(a)(2)
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "credit_access",
        }
    )
    
    # Fetch credit score
    score = await credit.get_credit_score(user_id)
    return score
```

This is **automatically handled** by `add_credit()` helper.

#### 3. FCRA Compliance Checklist

Before deploying credit monitoring in production:

- [x] **User Consent**: Implement consent workflow with clear disclosure
- [x] **Permissible Purpose Logging**: Log all credit accesses (done by `add_credit()`)
- [ ] **Adverse Action Notices**: If denying credit based on report, send notice to user
- [ ] **Data Retention Policy**: Define retention period per state laws (typically 2-7 years)
- [ ] **Security**: Encrypt credit data at rest and in transit
- [ ] **Access Controls**: Restrict credit report access to authorized personnel only
- [ ] **Audit Trail**: Maintain tamper-proof logs of all credit accesses
- [ ] **Privacy Policy**: Disclose credit monitoring in privacy policy
- [ ] **FCRA Disclosures**: Provide required disclosures to users
- [ ] **Legal Review**: Have legal counsel review implementation before production

### Sample FCRA Disclosure Text

**Example user-facing disclosure** (consult legal counsel before using):

> **Credit Monitoring Authorization**
>
> By checking this box, you authorize [Company Name] to access your credit report from Experian for the purpose of providing you with credit monitoring services. This is a "consumer disclosure" under the Fair Credit Reporting Act (FCRA §604(a)(2)).
>
> Your credit report will be used solely to:
> - Display your current credit score
> - Show your credit report details
> - Notify you of changes to your credit score
>
> We will NOT use your credit report for:
> - Making credit decisions
> - Employment screening
> - Insurance underwriting
>
> You may revoke this authorization at any time by contacting support.
>
> [ ] I authorize credit monitoring

### Adverse Action Requirements

If your app makes **credit decisions** based on credit reports (lending, insurance, employment), you MUST send **Adverse Action Notices**:

**Required elements** (FCRA §615):
1. Name and address of the credit bureau
2. Statement that bureau did not make the decision
3. User's right to dispute inaccurate information
4. User's right to free credit report within 60 days

**Example adverse action notice** (simplified):

```python
from fin_infra.credit import send_adverse_action_notice

# If denying loan application
await send_adverse_action_notice(
    user_id=user_id,
    decision="denied",
    reason="Insufficient credit history",
    bureau="experian",
    bureau_contact="Experian, P.O. Box 9595, Allen, TX 75013, 1-888-397-3742",
)
```

**Note**: Most fintech credit monitoring apps (like Credit Karma) do NOT make credit decisions, so adverse action notices are NOT required. This only applies if you're a lender, insurer, or employer using credit reports for decisions.

### FCRA Penalties

Violations of FCRA can result in:
- **Civil penalties**: $100 - $1,000 per violation
- **Actual damages**: Compensation for harm caused
- **Punitive damages**: For willful violations
- **Attorney fees**: Defendants pay plaintiff's legal costs
- **Criminal penalties**: Up to $5,000 fine and 1 year imprisonment for knowing violations

**Critical**: Consult legal counsel before deploying credit monitoring features in production.

### Recommended Reading

- [FTC: Fair Credit Reporting Act (Full Text)](https://www.ftc.gov/legal-library/browse/statutes/fair-credit-reporting-act)
- [CFPB: Credit Reports and Scores](https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/)
- [FTC: Summary of Rights Under FCRA](https://www.consumer.ftc.gov/articles/pdf-0096-fair-credit-reporting-act.pdf)
- [ADR-0011: Compliance Posture](./adr/0011-compliance-posture.md)

**Disclaimer**: This documentation is NOT legal advice. Consult with qualified legal counsel before deploying credit monitoring in production.

## FCRA Compliance Notes

### Legal Requirements

1. **User Consent**: Users must consent to credit pulls
2. **Permissible Purpose**: All pulls must have valid FCRA purpose
3. **Adverse Action Notices**: If credit decision is based on report, notify user
4. **Data Retention**: Credit reports must be retained per state laws
5. **Security**: PII must be encrypted at rest and in transit

### Implementation Checklist

- [ ] User consent workflow (checkbox, signature, etc.)
- [ ] Permissible purpose tracking (log all accesses)
- [ ] Adverse action notice generation (if applicable)
- [ ] Data retention policy (see ADR-0011, docs/compliance.md)
- [ ] PII encryption (use svc-infra.security)
- [ ] Access logging (use fin_infra.compliance)

### Recommended Reading

- [FTC: Fair Credit Reporting Act](https://www.ftc.gov/legal-library/browse/statutes/fair-credit-reporting-act)
- [CFPB: Credit Reporting](https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/)
- [ADR-0011: Compliance Posture](./adr/0011-compliance-posture.md)
- [Compliance Guide](./compliance.md)

**Disclaimer**: This documentation is NOT legal advice. Consult with legal counsel before deploying credit monitoring in production.

## API Reference

### easy_credit()

```python
def easy_credit(provider: str | CreditProvider = "experian", **config) -> CreditProvider
```

**Create configured credit provider with environment variable auto-detection.**

**Args**:
- `provider` (str | CreditProvider): Bureau name or CreditProvider instance
  - `"experian"` (default): Experian provider
  - `"equifax"`: Equifax provider (future)
  - `"transunion"`: TransUnion provider (future)
  - `CreditProvider` instance: Use directly
- `**config`: Optional configuration overrides
  - `api_key` (str): API key (overrides env)
  - `environment` (str): "sandbox" or "production" (overrides env)

**Returns**: Configured `CreditProvider` instance

**Environment Variables**:
- `EXPERIAN_API_KEY`: API key for Experian API
- `EXPERIAN_CLIENT_ID`: Client ID (if required)
- `EXPERIAN_ENVIRONMENT`: "sandbox" or "production" (default: sandbox)

**Examples**:

```python
# Zero config (uses EXPERIAN_API_KEY from env)
credit = easy_credit()

# Explicit provider
credit = easy_credit(provider="experian", api_key="...", environment="production")

# Custom provider instance
custom_provider = ExperianProvider(api_key="...", environment="production")
credit = easy_credit(provider=custom_provider)
```

### add_credit_monitoring()

```python
def add_credit_monitoring(
    app: FastAPI,
    *,
    provider: str | CreditProvider | None = None,
    prefix: str = "/credit",
    cache_ttl: int = 86400,
    **config
) -> CreditProvider
```

**Wire credit monitoring routes to FastAPI app.**

**Mounts routes**:
- `GET {prefix}/score` - Get current credit score (cached)
- `GET {prefix}/report` - Get full credit report (cached)
- `POST {prefix}/subscribe` - Subscribe to score change webhooks
- `GET {prefix}/history` - Get score history (future)

**Args**:
- `app` (FastAPI): FastAPI application
- `provider` (str | CreditProvider | None): Bureau name or CreditProvider instance (default: "experian")
- `prefix` (str): Route prefix (default: "/credit")
- `cache_ttl` (int): Cache TTL in seconds (default: 86400 = 24h)
- `**config`: Additional configuration passed to easy_credit()

**Returns**: Configured `CreditProvider` instance

**Example**:

```python
from fastapi import FastAPI
from fin_infra.credit.add import add_credit_monitoring

app = FastAPI()
credit = add_credit_monitoring(app, provider="experian")

# Routes available:
# GET /credit/score?user_id=user123
# GET /credit/report?user_id=user123
# POST /credit/subscribe?user_id=user123&webhook_url=...
```

## Testing

### Unit Tests

```bash
# Run credit tests
poetry run pytest tests/unit/test_credit.py -v

# All 22 tests pass with mock data
```

### Acceptance Tests

**v1**: No acceptance tests (requires real Experian API key)

**v2**: Will add acceptance tests with sandbox credentials

```bash
# Future: Run acceptance tests with sandbox credentials
EXPERIAN_API_KEY=sandbox_key poetry run pytest tests/acceptance/test_credit_experian_acceptance.py -v
```

## v1 Implementation Status

### Completed ✅

- [x] ADR-0012: Credit monitoring architecture
- [x] Data models: CreditScore, CreditReport, CreditAccount, CreditInquiry, PublicRecord
- [x] ExperianProvider (mock implementation)
- [x] easy_credit() one-liner
- [x] add_credit_monitoring() FastAPI helper
- [x] Unit tests (22 tests, all passing)
- [x] Documentation (this file)

### Deferred to v2 ⏸️

- [ ] Real Experian API integration (requires API key)
- [ ] svc-infra.cache integration (24h TTL)
- [ ] svc-infra.webhooks integration (score change notifications)
- [ ] Compliance event logging (FCRA permissible purpose)
- [ ] svc-infra dual routers (user_router for auth)
- [ ] svc-infra scoped docs (landing page card)
- [ ] Equifax provider
- [ ] TransUnion provider
- [ ] Acceptance tests (sandbox credentials)
- [ ] Score history tracking
- [ ] Dispute management

## Related Documentation

- [ADR-0012: Credit Monitoring Architecture](./adr/0012-credit-monitoring.md)
- [ADR-0011: Compliance Posture](./adr/0011-compliance-posture.md)
- [Compliance Guide](./compliance.md)
- [svc-infra Cache](../../svc-infra/docs/cache.md)
- [svc-infra Webhooks](../../svc-infra/docs/webhooks.md)

## Support

**Experian API**: https://developer.experian.com/  
**FCRA Guidance**: https://www.ftc.gov/legal-library/browse/statutes/fair-credit-reporting-act  
**Issues**: Report issues on GitHub

---

**Note**: v1 uses mock data only. Real bureau integration requires API keys and legal review before production deployment.
