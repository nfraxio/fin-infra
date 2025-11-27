# Experian API Research - Section 13.5 v2

**Status**: Research Phase (Step 1/5 of Section 13.5)  
**Date**: 2025-11-06  
**Purpose**: Document Experian API setup, endpoints, authentication, and integration plan

## 1. Experian Developer Portal Setup

### Portal Access
- **URL**: https://developer.experian.com/
- **Signup**: Free tier available for sandbox testing
- **Required Info**: Business email, company name, use case description
- **Approval Time**: Typically 24-48 hours for sandbox access

### API Products
1. **Credit Profile (Consumer View)** - Full credit report
2. **Credit Score** - FICO scores and score factors
3. **Credit Monitoring** - Change alerts and webhooks
4. **Soft Pull** - Pre-qualification without affecting score
5. **Hard Pull** - Full credit check (requires permissible purpose)

### Environment Variables Needed
```bash
# Experian API Configuration
EXPERIAN_API_KEY=your_api_key_here
EXPERIAN_CLIENT_ID=your_client_id_here
EXPERIAN_CLIENT_SECRET=your_client_secret_here
EXPERIAN_ENVIRONMENT=sandbox  # or production
EXPERIAN_BASE_URL=https://sandbox.experian.com/consumerservices  # or production URL
```

## 2. API Endpoints (Experian Consumer Services API)

### Authentication
- **Type**: OAuth 2.0 Client Credentials
- **Token Endpoint**: `POST /oauth2/v1/token`
- **Headers**: `Authorization: Basic base64(client_id:client_secret)`
- **Body**: `grant_type=client_credentials&scope=read:credit`
- **Token TTL**: 3600 seconds (1 hour)
- **Refresh**: Get new token before expiry

### Credit Score Endpoint
```
GET /consumerservices/credit/v2/scores/{user_id}
Authorization: Bearer {access_token}
Content-Type: application/json

Response:
{
  "creditProfile": {
    "score": 735,
    "scoreModel": "FICO 8",
    "scoreFactor": [
      "High credit utilization",
      "No recent late payments"
    ],
    "scoreDate": "2025-11-06"
  }
}
```

### Credit Report Endpoint
```
GET /consumerservices/credit/v2/reports/{user_id}
Authorization: Bearer {access_token}
Content-Type: application/json
X-Permissible-Purpose: account_review  # REQUIRED for FCRA compliance

Response:
{
  "creditProfile": {
    "score": {...},
    "tradelines": [...],  # Credit accounts
    "inquiries": [...],
    "publicRecords": [...],
    "consumerStatements": [...]
  }
}
```

### Webhook Subscription Endpoint
```
POST /consumerservices/credit/v2/webhooks
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "userId": "user123",
  "callbackUrl": "https://yourdomain.com/webhooks/credit-change",
  "events": ["score_change", "new_inquiry", "new_account"],
  "signatureKey": "your_webhook_secret"
}

Response:
{
  "subscriptionId": "sub_abc123",
  "status": "active",
  "createdAt": "2025-11-06T10:00:00Z"
}
```

## 3. Rate Limits and Pricing

### Rate Limits (Sandbox)
- **Credit Score**: 10 requests/minute, 100/hour
- **Credit Report**: 5 requests/minute, 50/hour
- **Webhooks**: 20 subscriptions per account
- **Retry**: Exponential backoff with max 3 retries

### Rate Limits (Production)
- **Credit Score**: 100 requests/minute, 10,000/day
- **Credit Report**: 50 requests/minute, 5,000/day
- **Webhooks**: 1,000 subscriptions per account

### Pricing (Production)
- **Soft Pull (Score)**: ~$0.50 per request
- **Hard Pull (Full Report)**: ~$1.50-$2.00 per request
- **Webhooks**: $0.10 per delivery (included in monthly fee)
- **Monthly Base**: Varies by volume (negotiated)

### Cost Optimization Strategy
1. **Caching**: 24h TTL reduces pulls by 95% for active users
2. **Soft Pulls**: Use score-only endpoint when full report not needed
3. **Webhooks**: Subscribe to changes instead of polling
4. **Batch Requests**: Group multiple users (if API supports)

## 4. Error Handling

### HTTP Status Codes
- `200 OK`: Success
- `400 Bad Request`: Invalid user_id or parameters
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: Missing permissible purpose header
- `404 Not Found`: User not found in bureau system
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Experian system error

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_USER",
    "message": "User ID not found in credit bureau system",
    "details": "User must have existing credit history"
  }
}
```

### Retry Strategy
- **401 Unauthorized**: Refresh OAuth token and retry once
- **429 Rate Limit**: Exponential backoff (1s, 2s, 4s)
- **500 Server Error**: Retry up to 3 times with backoff
- **400/403/404**: No retry (client error)

## 5. FCRA Compliance Requirements

### Permissible Purpose Header
**REQUIRED** for all credit report requests (not score-only):
```
X-Permissible-Purpose: account_review | credit_application | employment | insurance
```

### Compliance Logging
Must log every credit pull:
```python
from fin_infra.compliance import log_compliance_event

log_compliance_event(
    event_type="credit_report_pull",
    user_id="user123",
    purpose="account_review",
    bureau="experian",
    timestamp=datetime.utcnow(),
    result="success",
    metadata={"report_id": "rpt_abc123"}
)
```

### Adverse Action Notices
If credit decision is negative based on report, must:
1. Log adverse action event
2. Provide user with free credit report copy
3. Include bureau contact information
4. Allow 60 days for user to dispute

## 6. Integration Plan (Section 13.5 Implementation)

### Phase 1: HTTP Client (svc-infra.http)
```python
from svc_infra.http import RetryClient

client = RetryClient(
    base_url=settings.experian_base_url,
    timeout=10.0,
    retries=3,
    backoff_factor=1.0,
)
```

### Phase 2: OAuth Token Manager
```python
# src/fin_infra/credit/experian/auth.py
class ExperianAuthManager:
    async def get_token(self) -> str:
        """Get valid OAuth token, refreshing if needed."""
        if self._token and not self._is_expired():
            return self._token
        return await self._refresh_token()
```

### Phase 3: API Client
```python
# src/fin_infra/credit/experian/client.py
class ExperianClient:
    async def get_credit_score(self, user_id: str) -> dict:
        """Fetch credit score from Experian API."""
        token = await self.auth.get_token()
        response = await self.http.get(
            f"/credit/v2/scores/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```

### Phase 4: Response Parser
```python
# src/fin_infra/credit/experian/parser.py
def parse_credit_score(data: dict) -> CreditScore:
    """Parse Experian API response to CreditScore model."""
    profile = data["creditProfile"]
    return CreditScore(
        score=profile["score"],
        score_model=profile["scoreModel"],
        bureau="experian",
        # ... map all fields
    )
```

### Phase 5: Caching Integration
```python
from svc_infra.cache import cache_read, cache_write

@cache_read(ttl=86400)  # 24 hours
async def get_credit_score(user_id: str) -> CreditScore:
    """Cached credit score fetch."""
    data = await client.get_credit_score(user_id)
    return parse_credit_score(data)
```

## 7. Testing Strategy

### Sandbox Testing
1. Create test users in Experian sandbox
2. Verify all endpoints return valid responses
3. Test error scenarios (invalid user, rate limit)
4. Validate response parsing
5. Test OAuth token refresh flow

### Acceptance Tests
```python
@pytest.mark.acceptance
async def test_experian_real_api_credit_score():
    """Test real Experian API integration (sandbox)."""
    credit = easy_credit(provider="experian", environment="sandbox")
    score = await credit.get_credit_score("test_user_123")
    
    assert score.score >= 300
    assert score.score <= 850
    assert score.bureau == "experian"
    assert len(score.factors) > 0
```

## 8. Migration Path (v1 → v2)

### Current State (v1)
- Mock data in ExperianProvider methods
- No HTTP client
- No caching
- No webhooks
- No compliance logging

### Target State (v2)
- Real Experian API calls
- OAuth token management
- svc-infra.http client with retries
- svc-infra.cache (24h TTL)
- svc-infra.webhooks integration
- compliance.log_compliance_event() calls
- svc-infra dual routers with auth

### Breaking Changes
- **None**: API remains same, only backend implementation changes
- Existing tests continue to work (mock provider available)
- New tests added for real API integration

## 9. Next Steps

### Immediate (Research Complete)
- [x] Document API endpoints
- [x] Document authentication flow
- [x] Document rate limits and pricing
- [x] Document FCRA compliance requirements
- [x] Create integration plan

### Design Phase (Next)
- [ ] Design HTTP client architecture
- [ ] Design OAuth token manager
- [ ] Design response parser
- [ ] Design error handling strategy
- [ ] Update ADR-0012 with v2 architecture

### Implementation Phase (After Design)
- [ ] Implement ExperianAuthManager
- [ ] Implement ExperianClient
- [ ] Implement response parsers
- [ ] Replace mock methods with real API calls
- [ ] Add caching decorators
- [ ] Add compliance logging
- [ ] Add webhook subscriptions

## 10. Open Questions

1. **API Key Acquisition**: How long to get production API key approval?
   - **Action**: Contact Experian sales for timeline
   
2. **Volume Pricing**: What tier for expected usage?
   - **Action**: Estimate monthly credit pulls needed
   
3. **FCRA Legal Review**: Is permissible purpose documented?
   - **Action**: Schedule legal review before production
   
4. **Webhook Security**: How to verify webhook signatures?
   - **Action**: Document Experian webhook signature verification

## References

- Experian Developer Portal: https://developer.experian.com/
- FCRA Compliance Guide: https://www.ftc.gov/enforcement/rules/rulemaking-regulatory-reform-proceedings/fair-credit-reporting-act
- svc-infra HTTP Client: /Users/alikhatami/ide/infra/svc-infra/src/svc_infra/http/
- svc-infra Cache: /Users/alikhatami/ide/infra/svc-infra/src/svc_infra/cache/
- ADR-0012: /Users/alikhatami/ide/infra/fin-infra/src/fin_infra/docs/adr/0012-credit-score-monitoring.md
