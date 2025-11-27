# Recurring Detection V2 Verification Guide

This guide explains how to verify that LLM-enhanced recurring detection meets production targets:
- **Accuracy**: V2 achieves 92%+ vs V1's 85% baseline
- **Cost**: Effective cost <$0.001/user/month with 95%+ cache hit rate

## Overview

Two verification scripts measure production readiness:

1. **`benchmark_recurring_accuracy.py`**: Measures detection accuracy on labeled datasets
2. **`measure_recurring_costs.py`**: Simulates production traffic to measure costs and cache effectiveness

## Accuracy Benchmarking

### Quick Start

```bash
# Run V1 vs V2 comparison (requires GOOGLE_API_KEY)
GOOGLE_API_KEY=your_key poetry run python scripts/benchmark_recurring_accuracy.py --compare

# Test V1 only (no API key needed)
poetry run python scripts/benchmark_recurring_accuracy.py --v1-only

# Test V2 only
GOOGLE_API_KEY=your_key poetry run python scripts/benchmark_recurring_accuracy.py --v2-only
```

### Custom Dataset

Create a labeled dataset JSON file:

```json
[
  {
    "merchant_name": "NFLX*SUB #12345",
    "canonical_merchant": "netflix",
    "amounts": [15.99, 15.99, 15.99, 15.99, 15.99, 15.99],
    "dates": ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-01"],
    "is_recurring": true,
    "pattern_type": "simple",
    "category": "subscription"
  },
  {
    "merchant_name": "City Electric",
    "canonical_merchant": "city electric",
    "amounts": [45.5, 52.3, 48.75, 54.2, 58.9, 62.4],
    "dates": ["2024-01-15", "2024-02-15", "2024-03-15", "2024-04-15", "2024-05-15", "2024-06-15"],
    "is_recurring": true,
    "pattern_type": "seasonal",
    "category": "utility"
  }
]
```

Run benchmark:

```bash
poetry run python scripts/benchmark_recurring_accuracy.py --dataset path/to/labeled_data.json --compare
```

### Understanding Results

The script outputs:

```
==============================================================
  V2 Benchmark Results
==============================================================
Total Transactions:     100
Correct Predictions:    94
Overall Accuracy:       94.0%
False Positives:        3 (3.0%)
False Negatives:        3 (3.0%)

Breakdown by Category:
  Merchant Grouping:    96.0%
  Variable Detection:   90.0%
  Simple Patterns:      98.0%

Performance:
  Avg Processing Time:  45.23 ms
  Total Cost:           $0.0012

Comparison vs V1:
  Accuracy:             +9.0%
  False Positive Rate:  -3.0%
  Merchant Grouping:    +16.0%
  Variable Detection:   +20.0%
==============================================================

==============================================================
  Target Verification
==============================================================
V1 Targets:
  Accuracy ≥85%:        86.0% ✓
  False Positives ≤8%:  6.0% ✓

V2 Targets:
  Accuracy ≥92%:        94.0% ✓
  False Positives <5%:  3.0% ✓
  Variable Detection ≥88%: 90.0% ✓
  Merchant Grouping ≥95%:  96.0% ✓
==============================================================
```

**Targets**:
- ✅ V1: 85%+ accuracy, ≤8% false positives
- ✅ V2: 92%+ accuracy, <5% false positives, 88%+ variable detection, 95%+ merchant grouping

## Cost Measurement

### Quick Start

```bash
# Simulate 100 users for 30 days (default)
poetry run python scripts/measure_recurring_costs.py

# Larger simulation: 1000 users for 60 days
poetry run python scripts/measure_recurring_costs.py --users 1000 --days 60

# A/B test mode: 10% LLM, 90% pattern-only
GOOGLE_API_KEY=your_key poetry run python scripts/measure_recurring_costs.py --ab-test --llm-percentage 10
```

### Understanding Results

```
==============================================================
  Cost Measurement Results
==============================================================
Simulation:
  Users:                1,000
  Days:                 30
  Total Requests:       45,230

Cache Effectiveness:
  Cache Hits:           42,150
  Cache Misses:         3,080
  Cache Hit Rate:       93.2%

LLM Usage:
  Total LLM Calls:      3,080
  Total LLM Cost:       $0.2464

Per-User Costs:
  Avg Requests/User/Day:  1.51
  Avg Cost/User/Day:      $0.000008
  Avg Cost/User/Month:    $0.000246
  Avg Cost/User/Year:     $0.0030

==============================================================
  Target Verification
==============================================================
Cache Hit Rate ≥95%:           93.2% ✗
Cost/User/Month <$0.001:       $0.000246 ✓

💡 To hit cost target, need ~95.5% cache hit rate
==============================================================
```

**Targets**:
- ✅ Cache hit rate: 95%+ (normalizations highly cacheable)
- ✅ Cost per user per month: <$0.001 (annual <$0.012)

### A/B Testing

For production rollout, start with 10% LLM-enabled users:

```bash
# Simulate A/B test
poetry run python scripts/measure_recurring_costs.py \
  --ab-test \
  --llm-percentage 10 \
  --users 1000 \
  --days 30
```

This measures:
- Cost delta between LLM and pattern-only groups
- Cache effectiveness with mixed traffic
- Accuracy improvement (combine with benchmark script)

## Production Verification Checklist

### Phase 1: Pre-Production Testing

- [ ] Run accuracy benchmark with V1-only: `--v1-only`
  - [ ] Verify V1 achieves 85%+ accuracy baseline
  - [ ] Verify V1 has ≤8% false positive rate
- [ ] Run accuracy benchmark with V2 (requires API key): `--v2-only`
  - [ ] Verify V2 achieves 92%+ accuracy
  - [ ] Verify V2 has <5% false positive rate
  - [ ] Verify variable detection ≥88%
  - [ ] Verify merchant grouping ≥95%
- [ ] Run cost simulation: `--users 1000 --days 30`
  - [ ] Verify cache hit rate ≥95%
  - [ ] Verify cost/user/month <$0.001

### Phase 2: A/B Test (10% LLM)

- [ ] Deploy with `enable_llm=True` for 10% of users
- [ ] Run cost measurement in production for 7 days
- [ ] Compare accuracy metrics:
  - [ ] LLM group: Track false positive/negative rates
  - [ ] Pattern-only group: Track same metrics
  - [ ] Statistical significance test (chi-square)
- [ ] Monitor costs:
  - [ ] LLM API costs (Gemini Flash usage)
  - [ ] Cache hit rate (should be 95%+)
  - [ ] Effective cost per user

### Phase 3: Gradual Rollout

Based on A/B test results:

- [ ] If accuracy improvement ≥7% AND cost <$0.001/user/month:
  - [ ] Increase to 25% LLM
  - [ ] Monitor for 7 days
  - [ ] Increase to 50% LLM
  - [ ] Monitor for 7 days
  - [ ] Increase to 100% LLM
- [ ] If accuracy improvement 5-7% OR cost $0.001-$0.002/user/month:
  - [ ] Consider partial rollout (50% max)
  - [ ] Optimize cache TTLs (increase from 7 days to 14 days)
  - [ ] Re-evaluate cost/accuracy tradeoff
- [ ] If accuracy improvement <5% OR cost >$0.002/user/month:
  - [ ] Keep at 10% or disable LLM
  - [ ] Focus on improving V1 pattern matching

## Interpreting Results

### Accuracy Metrics

| Metric | V1 Target | V2 Target | Meaning |
|--------|-----------|-----------|---------|
| Overall Accuracy | 85%+ | 92%+ | Correct recurring/non-recurring classification |
| False Positive Rate | ≤8% | <5% | Non-recurring incorrectly marked as recurring |
| False Negative Rate | — | — | Recurring missed (less critical) |
| Variable Detection | 70%+ | 88%+ | Seasonal utility bills correctly detected |
| Merchant Grouping | 80%+ | 95%+ | Name variants matched to canonical merchant |

### Cost Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| Cache Hit Rate | 95%+ | Percentage of merchant normalizations served from cache |
| Cost/User/Month | <$0.001 | Effective LLM cost per active user per month |
| Cost/User/Year | <$0.012 | Annualized cost (budget: $0.003, safety margin 4x) |

### When to Optimize

**Cache hit rate <95%**:
- Increase cache TTL from 7 days to 14 days
- Pre-warm cache with common merchants (Netflix, Spotify, etc.)
- Consider adding merchant alias lookup before LLM call

**Cost/user/month >$0.001**:
- Reduce LLM percentage (A/B test)
- Increase cache TTL
- Batch LLM requests (if provider supports)
- Switch to cheaper model (e.g., Gemini Nano when available)

**Accuracy <92%**:
- Review false positives/negatives
- Improve few-shot prompts with production examples
- Add domain-specific rules for edge cases
- Consider fine-tuning (future enhancement)

## Troubleshooting

### Benchmark Script Issues

**ImportError: No module named 'ai_infra'**:
```bash
# Install ai-infra dependency
poetry add ai-infra --group dev
```

**Benchmark fails with "GOOGLE_API_KEY not set"**:
```bash
# Export API key
export GOOGLE_API_KEY=your_key_here

# Or run V1 only
poetry run python scripts/benchmark_recurring_accuracy.py --v1-only
```

**Low accuracy on custom dataset**:
- Verify dataset labels are correct (is_recurring, pattern_type)
- Check that transactions have 4+ occurrences (needed for pattern detection)
- Ensure dates are ISO format (YYYY-MM-DD)

### Cost Measurement Issues

**Simulated costs seem too high**:
- Check if cache is working (should see 95%+ hit rate)
- Verify user activity simulation is realistic
- Consider that simulation might be more active than real users

**Cache hit rate lower than expected**:
- Ensure Redis is running (if using real cache)
- Check cache TTL settings (should be 7 days for normalizations)
- Verify merchant names are normalized for cache keys (lowercase)

## Production Monitoring

After deploying V2, monitor these metrics:

1. **LLM API Costs** (Grafana dashboard):
   - Daily LLM spend
   - Cost per user per day
   - Cost trend over time

2. **Cache Performance**:
   - Hit rate by hour/day
   - Cache size (number of keys)
   - Eviction rate

3. **Accuracy Signals** (user feedback):
   - "Not a subscription" reports
   - "Missing subscription" reports
   - Merchant name correction rate

4. **Performance**:
   - P50/P95/P99 latency for recurring detection
   - LLM call timeout rate
   - Fallback to V1 rate (when LLM fails)

## Reporting

After running benchmarks, document results:

```markdown
## V2 Verification Results (YYYY-MM-DD)

### Accuracy Benchmark
- Dataset: [100 labeled transactions | Production sample]
- V1 Accuracy: XX.X% (target: 85%+)
- V2 Accuracy: XX.X% (target: 92%+)
- V2 Variable Detection: XX.X% (target: 88%+)
- V2 Merchant Grouping: XX.X% (target: 95%+)
- **Status**: [✓ PASS | ✗ FAIL]

### Cost Measurement
- Simulation: [1000 users, 30 days]
- Cache Hit Rate: XX.X% (target: 95%+)
- Cost/User/Month: $X.XXXXXX (target: <$0.001)
- Cost/User/Year: $X.XXXX (target: <$0.012)
- **Status**: [✓ PASS | ✗ FAIL]

### Recommendation
[Deploy to 10% | Deploy to 100% | Optimize and re-test | Do not deploy]
```

## Next Steps

After verification:

1. **If targets met**: Proceed with A/B test deployment (10% LLM)
2. **If accuracy below target**: Review prompts, add examples, test different models
3. **If cost above target**: Increase cache TTL, optimize prompts, consider cheaper models
4. **If cache hit rate low**: Pre-warm cache, increase TTL, add merchant aliases

For questions or issues, see `src/fin_infra/docs/recurring-detection-v2.md`.
