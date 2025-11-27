# ADR Template for fin-infra

All Architecture Decision Records (ADRs) in fin-infra must include a svc-infra reuse assessment.

## Template

```markdown
# ADR-NNNN: [Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: YYYY-MM-DD
**Authors**: [Names]

## Context

[Describe the problem or requirement that needs to be addressed]

## svc-infra Reuse Assessment

**MANDATORY: Complete BEFORE proposing solution**

### What was checked in svc-infra?
- [ ] Searched svc-infra README for related functionality
- [ ] Reviewed svc-infra modules: [list specific modules checked]
- [ ] Checked svc-infra docs: [list specific docs reviewed]
- [ ] Examined svc-infra source: [list files/directories examined]

### Findings
- **Does svc-infra provide this functionality?** [Yes/No/Partially]
- **If Yes**: Why can't we use svc-infra's implementation?
  - [Explain specific limitations or incompatibilities]
- **If Partially**: What parts can we reuse?
  - [List specific svc-infra modules/functions to import]
  - [Explain what fin-infra must implement]

### Classification
- [ ] Type A: Financial-specific (banking, market data, credit, tax, cashflows)
- [ ] Type B: Backend infrastructure (must use svc-infra)
- [ ] Type C: Hybrid (use svc-infra for infrastructure, fin-infra for provider logic)

### Reuse Plan
If Type B or C, document specific svc-infra imports:
```python
# Example:
from svc_infra.logging import setup_logging
from svc_infra.cache import init_cache, cache_read
from svc_infra.http import http_client_with_retry
```

## Decision

[Describe the decision made, including:]
- What fin-infra will implement (if anything)
- What will be imported from svc-infra
- How the two will integrate

## Consequences

### Positive
- [List benefits of this decision]
- [Include benefits of reusing svc-infra where applicable]

### Negative
- [List drawbacks or trade-offs]

### Neutral
- [List neutral consequences]

## Implementation Notes

### svc-infra Integration
- Modules to import: [list]
- Configuration required: [describe]
- Example code: [provide]

### fin-infra Implementation
- New modules: [list]
- Provider adapters: [list]
- Tests required: [describe]

## References

- Related ADRs: [list]
- svc-infra modules: [links to relevant svc-infra code]
- External docs: [links]

## Example Integrations

[Provide code examples showing fin-infra + svc-infra integration]

```

## ADR Approval Checklist

Before marking an ADR as "Accepted", verify:

- [ ] svc-infra reuse assessment is complete and thorough
- [ ] Classification (Type A/B/C) is clearly identified
- [ ] If Type B or C, svc-infra imports are documented
- [ ] No duplication of svc-infra functionality
- [ ] Integration examples are provided
- [ ] Tests cover both fin-infra and svc-infra integration points

## Rejection Criteria

An ADR will be REJECTED if:

- ❌ svc-infra reuse assessment is incomplete
- ❌ Proposes reimplementing svc-infra functionality without clear justification
- ❌ Classified as Type A but overlaps with backend infrastructure
- ❌ No integration examples provided for Type C decisions
- ❌ Does not document which svc-infra modules to use

## Examples

### Good ADR (Type A - Financial-specific)
```markdown
## svc-infra Reuse Assessment

### What was checked in svc-infra?
- Searched svc-infra for Plaid/banking integration: Not found
- Reviewed svc-infra/billing: Only Stripe/Adyen, not bank aggregation
- Conclusion: Banking aggregation is financial-specific

### Classification
- [x] Type A: Financial-specific

### Reuse Plan
Will use svc-infra for:
- Logging: `setup_logging()` for provider call logs
- Caching: `cache_read/cache_write` for account data
- HTTP: svc-infra's retry logic for API calls
```

### Bad ADR (Rejected - Duplicates svc-infra)
```markdown
## Decision

Implement fin-infra logging module with structured logging...

## Rejection Reason
❌ svc-infra already provides structured logging via `svc_infra.logging`.
Must use svc-infra's logging instead of implementing new logging.
```

### Good ADR (Type C - Hybrid)
```markdown
## svc-infra Reuse Assessment

### Classification
- [x] Type C: Hybrid

### Reuse Plan
svc-infra provides:
- API framework: `easy_service_app`
- Observability: `add_observability` for metrics
- Caching: `init_cache` for response caching

fin-infra provides:
- Provider client: Alpha Vantage API wrapper
- Data models: Quote, Candle, etc.
- Symbol normalization

### Integration
```python
from svc_infra.api.fastapi.ease import easy_service_app
from svc_infra.cache import cache_read
from fin_infra.markets import AlphaVantageProvider

app = easy_service_app()
provider = AlphaVantageProvider()

@app.get("/quote/{symbol}")
@cache_read(ttl=60)
def get_quote(symbol: str):
    return provider.quote(symbol)
```
```
