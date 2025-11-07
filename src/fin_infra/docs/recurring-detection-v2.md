# Recurring Detection — V2 (LLM-Enhanced)

This document describes the V2 LLM-based recurring detection system implemented in `fin-infra`.

Summary
-------
- V2 adds LLM-assisted merchant normalization, variable-amount recurring detection, and subscription insights.
- Designed to be optional: the LLM wiring is behind `enable_llm` / `enable_cache` flags and falls back to deterministic logic.

Quickstart
----------
1. Install dependencies and enable `ai-infra` in your environment per repo README.
2. Set `GOOGLE_API_KEY` (or other provider API keys) to run acceptance tests or to enable real LLM calls.
3. Use the helpers:

```py
from fin_infra.recurring.normalizers import MerchantNormalizer
from fin_infra.recurring.detectors_llm import VariableDetectorLLM
from fin_infra.recurring.insights import SubscriptionInsightsGenerator

norm = MerchantNormalizer(provider="google", enable_cache=False)
det = VariableDetectorLLM(provider="google")
gen = SubscriptionInsightsGenerator(provider="google", enable_cache=False)

# normalize
result = await norm.normalize("NFLX*SUB")

# detect
amounts = [45.5, 52.3, 48.75]
date_pattern = "Monthly (15th ±3 days)"
pattern = await det.detect("City Electric", amounts, date_pattern)

# insights
insights = await gen.generate([{"merchant":"Netflix","amount":15.99,"cadence":"monthly"}])
```

Design notes
------------
- Merchant normalization uses few-shot prompting with model-specific templates. The implementation gracefully degrades to simple rule-based heuristics when LLM not available.
- Variable detection expects a list of numeric amounts plus a date pattern string (e.g., "Monthly (15th ±3 days)"). It returns a `VariableRecurringPattern` Pydantic model with `expected_range: Optional[tuple[float,float]]`.
- Insights generator accepts a list of subscriptions and returns `SubscriptionInsights` (summary, top_subscriptions, recommendations, total_monthly_cost, potential_savings).

Testing
-------
- Unit tests: `tests/unit/test_recurring_normalizers.py`, `tests/unit/test_recurring_detectors_llm.py`, `tests/unit/test_recurring_insights.py` — run with `pytest tests/unit -q`.
- Acceptance tests: `tests/acceptance/test_recurring_llm.py`. These tests are skipped unless `GOOGLE_API_KEY` (or other provider key) is set. They exercise real model calls and should be used sparingly.

Cost & Budgeting
-----------------
- Each LLM call increments in-memory budget counters (`_daily_cost`, `_monthly_cost`) to protect costs. Defaults: `$0.10/day`, `$2.00/month`.
- For production, replace tracking with Redis or a shared store.

Troubleshooting
---------------
- If tests fail with `AttributeError: ... does not have the attribute 'CoreLLM'` ensure you have `ai-infra` installed or mocks in tests. The code imports `CoreLLM` with try/except to allow tests to patch it at module-level.
- Cache-related unit tests are skipped locally unless you enable `svc-infra` cache shims in your environment; run those as part of an integration/acceptance step with Redis.

Notes
-----
This doc is intentionally concise; for in-depth design rationale see `src/fin_infra/docs/adr/` (if present) or reach out to the maintainers.
