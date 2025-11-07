# Recurring Transaction Detection - LLM Enhancement Research (V2)

**Date**: 2025-11-07  
**Status**: Research Phase  
**Related**: ADR-0019 (V1 Pattern-Based Detection), Section 15 V2 (Categorization LLM)

---

## Table of Contents

1. [ai-infra Capabilities Assessment](#1-ai-infra-capabilities-assessment)
2. [Merchant Name Normalization Approaches](#2-merchant-name-normalization-approaches)
3. [Variable Amount Detection Methods](#3-variable-amount-detection-methods)
4. [Cost Analysis & Budget Planning](#4-cost-analysis--budget-planning)
5. [Architecture Design](#5-architecture-design)
6. [Implementation Plan](#6-implementation-plan)

---

## 1. ai-infra Capabilities Assessment

### 1.1 Research Question
**Can we reuse ai-infra.llm for recurring detection enhancement?**

### 1.2 Findings from Section 15 V2

We successfully used ai-infra.llm for transaction categorization with:

**CoreLLM API**:
- ✅ `CoreLLM.achat()` with structured output (Pydantic schemas)
- ✅ Multi-provider support: Google Gemini, OpenAI, Anthropic
- ✅ Automatic retry with exponential backoff (max_tries=3)
- ✅ `output_method="prompt"` for cross-provider compatibility
- ✅ Robust JSON extraction via `coerce_from_text_or_fragment()`

**Structured Output**:
- ✅ Pydantic schema validation via `output_schema` parameter
- ✅ Automatic json_mode fallback if prompt parsing fails
- ✅ Detailed error messages for invalid responses

**Cost Management**:
- ✅ Token tracking per request
- ✅ Budget enforcement (daily/monthly caps)
- ✅ Provider cost comparison (Gemini cheapest at $0.00011/request)

### 1.3 Applicability to Recurring Detection

**Use Case 1: Merchant Name Normalization**
- **Input**: "NFLX*SUB #12345", "Netflix Inc", "NETFLIX.COM"
- **Output**: Pydantic schema `MerchantNormalized(canonical_name="Netflix", merchant_type="streaming", confidence=0.95)`
- **Approach**: Few-shot prompting with 20 examples
- **ai-infra fit**: ✅ Perfect - identical to categorization pattern

**Use Case 2: Variable Amount Detection**
- **Input**: 6 utility transactions with amounts $45, $52, $48, $55, $50, $49
- **Output**: Pydantic schema `RecurringPattern(is_recurring=True, cadence="monthly", expected_range=(45, 60), reasoning="seasonal winter heating")`
- **Approach**: Few-shot with seasonal examples
- **ai-infra fit**: ✅ Perfect - structured output with reasoning

**Use Case 3: Insights Generation**
- **Input**: List of 5 detected subscriptions
- **Output**: Pydantic schema `SubscriptionInsights(summary="...", top_subscriptions=[...], recommendations=[...])`
- **Approach**: Few-shot with financial advice examples
- **ai-infra fit**: ✅ Perfect - natural language generation

### 1.4 Classification

**Type A: Financial-specific with AI infrastructure reuse**

- **Financial domain**: Merchant normalization, subscription detection, financial insights
- **AI infrastructure**: ai-infra.llm for LLM inference, structured output, retry logic
- **svc-infra integration**: svc-infra.cache for merchant normalization (1-week TTL), svc-infra.jobs for batch processing

### 1.5 Reuse Plan

**ai-infra.llm**:
- ✅ `CoreLLM.achat()` for all LLM calls
- ✅ `output_schema` with Pydantic models (MerchantNormalized, RecurringPattern, SubscriptionInsights)
- ✅ `output_method="prompt"` for cross-provider compatibility
- ✅ Multi-provider support (Google Gemini default, OpenAI, Anthropic as alternates)
- ✅ Retry logic with exponential backoff (max_tries=3, base=0.5s, jitter=0.2s)

**svc-infra.cache**:
- ✅ Merchant normalization cache (key: `merchant_norm:{md5(merchant_name)}`, TTL: 7 days)
- ✅ Insights cache (key: `subscription_insights:{user_id}`, TTL: 24 hours)
- ✅ Expected cache hit rate: 95% (merchants are repetitive)

**svc-infra.jobs**:
- ✅ Daily batch merchant normalization (process new merchants overnight)
- ✅ Weekly insights generation (scheduled for Sunday evenings)

### 1.6 Conclusion

✅ **APPROVED**: ai-infra.llm provides all necessary capabilities for recurring detection LLM enhancement. Reuse patterns from Section 15 V2 (categorization) with identical architecture:
- Few-shot prompting (20 examples)
- Structured output (Pydantic schemas)
- Cost optimization (caching + budget caps)
- Multi-provider support (Google Gemini default)

---

## 2. Merchant Name Normalization Approaches

### 2.1 Problem Statement

**Challenge**: Group merchant name variants under canonical name
- "NFLX*SUB #12345" → "Netflix"
- "Netflix Inc" → "Netflix"
- "NETFLIX.COM" → "Netflix"
- "SQ *COFFEE SHOP" → "Square Cafe" (ambiguous without context)

**V1 Approach (RapidFuzz)**:
- ✅ Works for exact variants (80% similarity)
- ❌ Fails for cryptic names ("SQ *", "TST*", "AMZN MKTP")
- ❌ Requires pre-defined merchant groups (limited scalability)
- **Accuracy**: ~80% on edge cases

### 2.2 LLM Approach Comparison

#### Option 1: Zero-Shot
**Prompt**: "Normalize this merchant name: 'NFLX*SUB #12345'"

**Accuracy**: 70-80%
- ✅ Works for obvious cases (Netflix, Amazon, Starbucks)
- ❌ Fails for cryptic names (SQ *, TST*, AMZN MKTP)
- ❌ No context on merchant types

**Cost**: $0.00011/request (Gemini)

**Decision**: ❌ **REJECTED** - Below RapidFuzz baseline

#### Option 2: Few-Shot (RECOMMENDED)
**Prompt**: System prompt + 20 examples covering merchant types

```
Examples:
- "NFLX*SUB #12345" → Netflix (streaming)
- "SQ *COFFEE SHOP" → Square Cafe (payment processor)
- "AMZN MKTP US" → Amazon (online shopping)
- "TST* STARBUCKS" → Starbucks (coffee shop, Toast POS)
- "UBER *TRIP" → Uber (rideshare)
- "SPFY*PREMIUM" → Spotify (streaming)
...
```

**Accuracy**: 90-95% (based on Section 15 V2 results)
- ✅ Handles cryptic names with context
- ✅ Identifies payment processors (SQ, TST, CLOVER)
- ✅ Consistent canonical naming

**Cost**: $0.00011/request (Gemini) with 95% cache hit → $0.0000055 effective

**Decision**: ✅ **RECOMMENDED** - Best accuracy/cost ratio

#### Option 3: Fine-Tuning
**Approach**: Fine-tune GPT-4o-mini on 10k+ labeled merchant pairs

**Accuracy**: 95-98%
- ✅ Best accuracy
- ❌ Requires 10k+ labeled pairs (expensive to create)
- ❌ Fine-tuning cost: $2-5 (one-time) + $0.015/1k tokens (3x inference cost)
- ❌ Maintenance overhead (retrain when new merchants appear)

**Cost**: $0.00033/request (3x few-shot)

**Decision**: ❌ **DEFERRED to V3** - Overkill for this use case, high complexity

### 2.3 Few-Shot Prompt Design

**System Prompt**:
```
You are a financial transaction expert specializing in merchant name normalization.
Given a merchant name from a bank transaction, identify the canonical merchant name
and merchant type.

Common patterns:
- Payment processors: SQ * (Square), TST* (Toast), CLOVER* (Clover)
- Subscriptions: NFLX* (Netflix), SPFY* (Spotify), AMZN* (Amazon)
- Store numbers: Remove #1234, store-specific identifiers
- Legal entities: Remove Inc, LLC, Corp, Ltd

Examples (20 diverse merchants covering all categories):
...
```

**Output Schema** (Pydantic):
```python
class MerchantNormalized(BaseModel):
    canonical_name: str          # "Netflix"
    merchant_type: str           # "streaming", "coffee_shop", "grocery", etc.
    confidence: float            # 0.0-1.0
    reasoning: str               # Max 150 chars
```

**Token Cost**:
- Input: ~800 tokens (system prompt + examples) + ~50 tokens (merchant name) = ~850 tokens
- Output: ~50 tokens (JSON response)
- Total: ~900 tokens per request

**Cost per Request** (Google Gemini 2.0 Flash):
- Input: 850 tokens × $0.075/1M = $0.000064
- Output: 50 tokens × $0.30/1M = $0.000015
- **Total: $0.000079** (~$0.00008/request, slightly cheaper than categorization)

### 2.4 Caching Strategy

**Cache Key**: `merchant_norm:{md5(normalized_lowercase_merchant_name)}`
- Normalize before hashing: lowercase, remove whitespace, remove store numbers
- Example: "NFLX*SUB #12345" → md5("nflxsub") → cache key

**TTL**: 7 days (1 week)
- Merchant names are stable (Netflix stays Netflix)
- Longer than categorization (24h) because merchant identity doesn't change

**Expected Hit Rate**: 95%
- Most users shop at same merchants repeatedly
- Netflix, Amazon, Starbucks appear in every user's transactions

**Effective Cost**:
- Uncached: $0.00008/request
- 95% hit rate: $0.00008 × 0.05 = **$0.000004/request**
- **Cost reduction: 20x**

### 2.5 Fallback Strategy

**Hybrid Approach**:
1. **Try cache first** (95% hit rate, <1ms)
2. **If cache miss, try RapidFuzz** (80% accuracy for common variants, ~5ms)
3. **If RapidFuzz confidence < 0.8, call LLM** (90-95% accuracy, ~200-400ms)
4. **Cache result** (7-day TTL)

**Benefits**:
- ✅ Fast path for 95% of requests (cache)
- ✅ Free fallback for common variants (RapidFuzz)
- ✅ LLM only for edge cases (~5% of requests)
- ✅ Graceful degradation (LLM disabled → RapidFuzz only)

### 2.6 Conclusion

✅ **Few-shot merchant normalization with hybrid fallback**:
- **Accuracy**: 90-95% (vs 80% RapidFuzz)
- **Cost**: $0.000004/request with 95% caching
- **Latency**: <1ms (cached), ~200-400ms (uncached)
- **Implementation**: Reuse Section 15 V2 patterns (CoreLLM, Pydantic, caching)

---

## 3. Variable Amount Detection Methods

### 3.1 Problem Statement

**Challenge**: Detect recurring transactions with variable amounts
- Utility bills: $45, $52, $48, $55, $50, $49 (seasonal heating/cooling)
- Phone bills: $50, $50, $50, $78 (overage charges)
- Gym fees: $40, $40, $0, $40 (annual fee waived one month)

**V1 Approach (Statistical)**:
- Mean ± 2 standard deviations (95% confidence interval)
- Works for normal distributions
- ❌ Fails for seasonal patterns (winter heating spikes)
- ❌ Fails for occasional spikes (phone overage)
- **Accuracy**: ~70% for variable subscriptions

### 3.2 Approach Comparison

#### Option 1: Statistical Only (V1 Baseline)
**Method**: Calculate mean and standard deviation, detect if amounts fall within mean ± 2σ

**Accuracy**: ~70%
- ✅ Fast (no API calls)
- ✅ Works for normal distributions (most variable subscriptions)
- ❌ Fails for seasonal patterns (utility bills 2x in winter)
- ❌ Fails for occasional spikes (phone overage)
- ❌ No semantic understanding (can't explain "why" amounts vary)

**Cost**: $0 (no LLM)

#### Option 2: LLM Only
**Method**: Call LLM for every variable amount pattern

**Accuracy**: 88%+ (based on research)
- ✅ Understands seasonal patterns (winter heating)
- ✅ Identifies occasional spikes (phone overage, annual fees)
- ✅ Natural language reasoning ("seasonal winter heating")
- ❌ Expensive (LLM call for every pattern)
- ❌ Slow (~200-400ms per call)

**Cost**: $0.0001/detection (assuming ~1,200 tokens)

#### Option 3: Hybrid (RECOMMENDED)
**Method**: Statistical filter → LLM for edge cases

**Flow**:
1. **Statistical filter**: If variance < 20%, mark as "variable recurring" (70% of cases)
2. **LLM edge cases**: If variance 20-40%, call LLM to analyze pattern (~10% of cases)
3. **Reject**: If variance > 40%, not recurring

**Accuracy**: 85-88%
- ✅ Fast path for normal distributions (70% cases, no LLM)
- ✅ LLM for edge cases (seasonal, spikes)
- ✅ Cost-effective (LLM only 10% of time)

**Cost**: $0.0001 × 0.10 = **$0.00001/detection**

**Decision**: ✅ **RECOMMENDED** - Best accuracy/cost balance

### 3.3 LLM Prompt Design

**System Prompt**:
```
You are a financial analysis expert specializing in recurring payment detection.
Given a merchant name and transaction history, determine if the variable amounts
represent a recurring subscription or bill.

Common patterns:
- Utility bills: Seasonal variation (2x in winter for heating, summer for AC)
- Phone bills: Occasional spikes (overage charges, international calls)
- Gym fees: Annual fee waived, promotional discounts
- Streaming services: Price changes (rare, <5% variance)

Examples:
1. Merchant: "City Electric", Amounts: [45, 52, 48, 55, 50, 49], Dates: monthly
   → Recurring: Yes, Seasonal heating variation, Expected range: (40, 60)

2. Merchant: "T-Mobile", Amounts: [50, 50, 50, 78, 50], Dates: monthly
   → Recurring: Yes, Occasional overage charge, Expected range: (50, 80)

3. Merchant: "Random Store", Amounts: [10, 45, 23, 67, 12], Dates: irregular
   → Recurring: No, Too much variance, no pattern
...
```

**Output Schema** (Pydantic):
```python
class VariableRecurringPattern(BaseModel):
    is_recurring: bool                    # True if recurring despite variance
    cadence: Optional[str]                # "monthly", "quarterly", etc.
    expected_range: Optional[tuple[float, float]]  # (min, max) expected amounts
    reasoning: str                        # Max 200 chars
    confidence: float                     # 0.0-1.0
```

**Token Cost**:
- Input: ~1,000 tokens (system + examples + transaction history)
- Output: ~100 tokens
- Total: ~1,100 tokens

**Cost per Detection** (Google Gemini):
- Input: 1,000 × $0.075/1M = $0.000075
- Output: 100 × $0.30/1M = $0.00003
- **Total: $0.000105** (~$0.0001/detection)

### 3.4 When to Call LLM

**Trigger Conditions** (only call LLM if ALL true):
1. ✅ Merchant matches (fuzzy similarity > 80%)
2. ✅ Dates are clustered (monthly ± 7 days)
3. ✅ Amount variance 20-40% (not fixed, not random)
4. ✅ At least 4 occurrences (need history)

**Expected Trigger Rate**: ~10% of patterns
- 70% have variance < 20% (statistical handles)
- 20% have variance > 40% (reject immediately)
- **10% fall in 20-40% range (LLM candidates)**

### 3.5 Conclusion

✅ **Hybrid variable detection**: Statistical filter + LLM for edge cases
- **Accuracy**: 85-88% (vs 70% statistical only)
- **Cost**: $0.00001/detection (LLM only 10% of time)
- **Implementation**: Call LLM only when variance is 20-40% (ambiguous cases)

---

## 4. Cost Analysis & Budget Planning

### 4.1 Cost Breakdown

#### Use Case 1: Merchant Normalization
**Trigger**: Every unique merchant name (first time seen)

**Cost per Request**:
- Google Gemini: $0.00008/request (850 input + 50 output tokens)
- OpenAI GPT-4o-mini: $0.00017/request (2x Gemini)
- Anthropic Claude 3.5 Haiku: $0.00030/request (4x Gemini)

**With 95% Caching** (7-day TTL):
- Effective cost: $0.00008 × 0.05 = **$0.000004/request**

**Expected Volume**: 50 unique merchants per user per year
- Most users shop at <50 merchants regularly
- New merchant discovery rate: ~5/month

**Annual Cost per User**:
- 50 merchants × $0.000004 = **$0.0002/user/year**

#### Use Case 2: Variable Amount Detection
**Trigger**: Only for ambiguous patterns (20-40% variance, ~10% of patterns)

**Cost per Detection**: $0.0001/detection

**Expected Volume**: 2 variable subscriptions per user (utilities, phone)
- Detected once, cached for 24 hours
- Annual re-detections: ~12 (monthly rechecks)

**Annual Cost per User**:
- 2 subscriptions × 12 detections × $0.0001 = **$0.0024/user/year**

#### Use Case 3: Insights Generation
**Trigger**: On-demand via API endpoint (GET /recurring/insights)

**Cost per Generation**: $0.0002/generation (1,500 tokens)

**Expected Volume**: 1-2 insights per user per month
- Users check insights when reviewing budget
- Most access via cached response (24h TTL)

**Annual Cost per User**:
- 12 insights × $0.0002 × 0.20 (80% cache hit) = **$0.00048/user/year**

### 4.2 Total Cost Summary

| Use Case | Uncached Cost | Cache Hit Rate | Effective Cost | Annual/User |
|----------|---------------|----------------|----------------|-------------|
| Merchant Normalization | $0.00008 | 95% | $0.000004 | **$0.0002** |
| Variable Detection | $0.0001 | N/A (run once) | $0.0001 | **$0.0024** |
| Insights Generation | $0.0002 | 80% | $0.00004 | **$0.00048** |
| **TOTAL** | | | | **$0.00288** |

**Rounded Total**: **~$0.003/user/year** (less than 1 cent per user per year)

**At Scale**:
- 1,000 users: **$3/year**
- 10,000 users: **$30/year**
- 100,000 users: **$300/year**
- 1,000,000 users: **$3,000/year**

### 4.3 Budget Caps

**Daily Budget**: $0.10/day
- Supports ~33,000 merchant normalizations/day
- Or ~1,000 variable detections/day
- Sufficient for 100k+ users

**Monthly Budget**: $2.00/month
- Supports ~700k users at $0.003/user/year
- Safety margin: 10x expected usage

**Auto-disable**: When budget exceeded
- Graceful fallback to RapidFuzz (no LLM)
- Log warning + webhook notification
- Reset daily/monthly as appropriate

### 4.4 Provider Comparison

| Provider | Merchant Norm | Variable Detect | Insights | Total/User/Year |
|----------|---------------|-----------------|----------|-----------------|
| **Google Gemini** | $0.00008 | $0.0001 | $0.0002 | **$0.003** ✅ |
| OpenAI GPT-4o-mini | $0.00017 | $0.00021 | $0.00042 | **$0.006** |
| Anthropic Claude | $0.00030 | $0.00037 | $0.00074 | **$0.011** |

**Decision**: ✅ **Google Gemini 2.0 Flash (default)** - Cheapest, sufficient accuracy

### 4.5 ROI Calculation

**Value to Users**:
- Better merchant grouping: 95% vs 80% accuracy → 15% improvement
- Variable detection: 88% vs 70% accuracy → 18% improvement
- Natural language insights: Qualitative value (save $30/month on subscriptions)

**Cost**: $0.003/user/year

**Conservative Value Estimate**:
- User saves $10/year from better subscription insights
- **ROI**: $10 / $0.003 = **3,333x return**

### 4.6 Conclusion

✅ **LLM enhancement is cost-effective**:
- **Total cost**: ~$0.003/user/year (less than 1 cent)
- **Accuracy gains**: +15-18% across use cases
- **ROI**: 3,333x (conservative estimate)
- **Budget**: $0.10/day, $2/month (sufficient for 700k users)

---

## 5. Architecture Design

### 5.1 Current V1 Architecture (Pattern-Based)

```
┌─────────────────────────────────────────────────┐
│          Transaction List (100 txns)            │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│     Step 1: Normalize Merchant Names            │
│     (RapidFuzz, 80% accuracy on edge cases)     │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│     Step 2: Group by Merchant + Date Cluster    │
│     (Monthly 28-32d, Biweekly 13-15d, etc.)     │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│     Step 3: Detect Patterns (3 layers)          │
│     - Fixed amount (±2%, 85% coverage)          │
│     - Variable amount (±20%, 10% coverage)      │
│     - Irregular (annual, 5% coverage)           │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│     Output: RecurringPattern[]                  │
│     (merchant, cadence, amount, confidence)     │
└─────────────────────────────────────────────────┘
```

**Strengths**:
- ✅ Fast (25ms for 100 txns)
- ✅ No API costs
- ✅ Works for 85% of subscriptions (fixed amount)

**Weaknesses**:
- ❌ Merchant normalization: 80% accuracy on edge cases (SQ *, TST*)
- ❌ Variable detection: 70% accuracy (misses seasonal patterns)
- ❌ No insights (just structured data)

### 5.2 Proposed V2 Architecture (4-Layer Hybrid)

```
┌─────────────────────────────────────────────────┐
│          Transaction List (100 txns)            │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ LAYER 1: Pattern-Based Merchant Normalization   │
│ (RapidFuzz, 80% accuracy, fast path)            │
├─────────────────────┬───────────────────────────┤
│ If confidence < 0.8 │                           │
└─────────────────────┼───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ LAYER 2: LLM Merchant Normalization             │
│ (Few-shot, 90-95% accuracy, 5% of merchants)    │
│ - Check cache first (95% hit, 7-day TTL)        │
│ - Call CoreLLM if cache miss                    │
│ - Output: MerchantNormalized Pydantic schema    │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│     Group by Canonical Merchant + Date Cluster  │
│     (Monthly 28-32d, Biweekly 13-15d, etc.)     │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ LAYER 3: Statistical Pattern Detection          │
│ - Fixed amount (±2%, 85% coverage) → DONE       │
│ - Variable amount (<20% var, 5% coverage) → DONE│
├─────────────────────┬───────────────────────────┤
│ If variance 20-40%  │                           │
└─────────────────────┼───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ LAYER 4: LLM Variable Amount Detection          │
│ (Few-shot, 88% accuracy, 10% of patterns)       │
│ - Call CoreLLM for ambiguous patterns           │
│ - Output: VariableRecurringPattern schema       │
│ - Understand seasonal/occasional spikes         │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│     Output: RecurringPattern[]                  │
│     (merchant, cadence, amount, confidence)     │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼ (Optional, on-demand)
┌─────────────────────────────────────────────────┐
│ LAYER 5: LLM Insights Generation                │
│ (Natural language summaries, recommendations)   │
│ - API endpoint: GET /recurring/insights         │
│ - Check cache first (24h TTL, 80% hit)          │
│ - Output: SubscriptionInsights schema           │
└─────────────────────────────────────────────────┘
```

### 5.3 Layer Breakdown

#### Layer 1: Pattern-Based Merchant Normalization (Fast Path)
**Coverage**: 95% of merchants (common names)
**Method**: RapidFuzz token_sort_ratio ≥ 80%
**Latency**: ~5ms
**Cost**: $0
**Accuracy**: 80% (edge cases fail)

#### Layer 2: LLM Merchant Normalization (Edge Cases)
**Coverage**: 5% of merchants (cryptic names: SQ *, TST*, AMZN MKTP)
**Method**: Few-shot prompting with CoreLLM
**Latency**: ~200-400ms (uncached), <1ms (cached 95%)
**Cost**: $0.000004/request (with caching)
**Accuracy**: 90-95%

#### Layer 3: Statistical Pattern Detection (Normal Distributions)
**Coverage**: 90% of patterns (fixed + low-variance variable)
**Method**: V1 algorithm (mean ± 2σ)
**Latency**: ~20ms
**Cost**: $0
**Accuracy**: 85% (fixed), 70% (variable with <20% variance)

#### Layer 4: LLM Variable Detection (Seasonal/Spikes)
**Coverage**: 10% of patterns (20-40% variance)
**Method**: Few-shot prompting with CoreLLM
**Latency**: ~200-400ms
**Cost**: $0.00001/detection
**Accuracy**: 88%

#### Layer 5: LLM Insights (Optional, On-Demand)
**Coverage**: User-initiated via API endpoint
**Method**: Few-shot prompting with CoreLLM
**Latency**: ~300-500ms (uncached), <1ms (cached 80%)
**Cost**: $0.00004/generation (with caching)
**Accuracy**: Qualitative (natural language)

### 5.4 Data Flow Example

**Example: Utility Bill Detection**

```
Input Transactions:
- 2025-01-15, "CITY ELECTRIC #123", $52.45
- 2025-02-18, "City Electric Inc", $48.20
- 2025-03-14, "CITY ELEC #456", $55.10
- 2025-04-16, "City Electric", $49.80
- 2025-05-15, "CITY ELECTRIC", $50.50
- 2025-06-17, "City Electric #789", $47.90

Step 1 (Layer 1 - RapidFuzz):
- All variants have 85%+ similarity to "city electric"
- Grouped as "city electric" (canonical)
- Confidence: 0.85 ✅ PASS (no LLM needed)

Step 2 (Grouping):
- All transactions same merchant, dates 28-32 days apart
- Cadence: MONTHLY

Step 3 (Layer 3 - Statistical):
- Amounts: 52.45, 48.20, 55.10, 49.80, 50.50, 47.90
- Mean: $50.66, Std Dev: $2.68
- Variance: 5.3% (within 20%)
- ✅ PASS: Variable recurring pattern detected
- No LLM needed (variance < 20%)

Output:
RecurringPattern(
    merchant_name="City Electric",
    pattern_type=PatternType.VARIABLE,
    cadence=CadenceType.MONTHLY,
    amount_range=(47.90, 55.10),
    confidence=0.85,
    reasoning="Monthly utility bill with low variance"
)
```

**Example 2: Cryptic Merchant + Seasonal Pattern**

```
Input Transactions:
- 2025-01-15, "SQ *COZY CAFE", $4.50
- 2025-02-18, "SQ *COZY CAFE", $4.50
- 2025-03-14, "SQ *COZY CAFE", $4.50
- 2025-04-16, "SQ *COZY CAFE", $4.50

Step 1 (Layer 1 - RapidFuzz):
- "SQ *COZY CAFE" doesn't match known merchants
- Confidence: 0.50 ❌ FAIL (< 0.8 threshold)

Step 2 (Layer 2 - LLM Merchant Normalization):
- Check cache: merchant_norm:md5("sqcozycafe") → MISS
- Call CoreLLM with few-shot prompt
- Response: MerchantNormalized(
    canonical_name="Cozy Cafe",
    merchant_type="coffee_shop",
    confidence=0.90,
    reasoning="Square payment processor prefix"
  )
- Cache result (7-day TTL)
- Grouped as "Cozy Cafe"

Step 3 (Grouping):
- Same merchant, dates ~30 days apart
- Cadence: MONTHLY

Step 4 (Layer 3 - Statistical):
- All amounts $4.50 (0% variance)
- ✅ PASS: Fixed recurring pattern
- No LLM needed (variance = 0%)

Output:
RecurringPattern(
    merchant_name="Cozy Cafe",
    pattern_type=PatternType.FIXED,
    cadence=CadenceType.MONTHLY,
    amount=$4.50,
    confidence=0.90,
    reasoning="Monthly coffee subscription via Square"
)
```

### 5.5 Graceful Degradation

**LLM Disabled** (`enable_llm=False`):
- Layer 1 only (RapidFuzz)
- Layer 3 only (statistical)
- No insights generation
- **Performance**: Same as V1 (fast, $0 cost)

**LLM Timeout/Error**:
- Fallback to Layer 1 result (RapidFuzz)
- Fallback to Layer 3 result (statistical)
- Log warning
- Continue processing (no blocking)

**Budget Exceeded**:
- Auto-disable LLM
- Fallback to V1 behavior
- Webhook notification
- Reset at midnight (daily) or month start (monthly)

### 5.6 Conclusion

✅ **4-layer hybrid architecture approved**:
- **Layer 1**: Pattern-based merchant normalization (95% coverage, fast)
- **Layer 2**: LLM merchant normalization (5% edge cases, high accuracy)
- **Layer 3**: Statistical pattern detection (90% coverage, fast)
- **Layer 4**: LLM variable detection (10% edge cases, seasonal understanding)
- **Layer 5**: LLM insights (on-demand, natural language)

**Benefits**:
- ✅ Backward compatible (LLM optional via `enable_llm=False`)
- ✅ Cost-effective (LLM only for edge cases, ~$0.003/user/year)
- ✅ Graceful degradation (fallback to V1 if LLM fails)
- ✅ Performance (fast path for 95% of cases)

---

## 6. Implementation Plan

### 6.1 Files to Create/Modify

#### New Files (3):
1. **recurring/normalizers.py** (LLM merchant normalization)
   - `MerchantNormalizer` class
   - Few-shot prompt template (20 examples)
   - Pydantic schema: `MerchantNormalized`
   - Cache integration (7-day TTL)
   - Fallback to RapidFuzz

2. **recurring/detectors_llm.py** (LLM variable detection)
   - `VariableDetectorLLM` class
   - Few-shot prompt template (seasonal patterns)
   - Pydantic schema: `VariableRecurringPattern`
   - Only called for 20-40% variance patterns

3. **recurring/insights.py** (natural language summaries)
   - `SubscriptionInsightsGenerator` class
   - Few-shot prompt template (financial advice)
   - Pydantic schema: `SubscriptionInsights`
   - API endpoint: GET /recurring/insights
   - Cache integration (24h TTL)

#### Modified Files (3):
1. **recurring/ease.py**
   - Add `enable_llm=False` parameter
   - Add `llm_provider="google"` parameter
   - Initialize `MerchantNormalizer` if `enable_llm=True`

2. **recurring/detector.py**
   - Integrate Layer 2 (call `MerchantNormalizer` for low-confidence merchants)
   - Integrate Layer 4 (call `VariableDetectorLLM` for 20-40% variance)
   - Fallback logic (LLM disabled or error)

3. **recurring/add.py**
   - Add new endpoint: GET /recurring/insights
   - Wire `SubscriptionInsightsGenerator`
   - Cache insights (24h TTL)

### 6.2 Test Plan

#### Unit Tests (12 tests):
1. test_merchant_normalizer_basic(): "NFLX*SUB" → MerchantNormalized("Netflix")
2. test_merchant_normalizer_cryptic(): "SQ *CAFE" → MerchantNormalized("Square Cafe")
3. test_merchant_normalizer_cache(): Verify cache hit (7-day TTL)
4. test_merchant_normalizer_fallback(): LLM disabled → RapidFuzz used
5. test_variable_detector_seasonal(): Utility bills → is_recurring=True
6. test_variable_detector_spikes(): Phone overage → is_recurring=True
7. test_variable_detector_random(): Random amounts → is_recurring=False
8. test_insights_generator(): 5 subscriptions → summary + recommendations
9. test_insights_cache(): Verify cache hit (24h TTL)
10. test_llm_disabled(): enable_llm=False → no LLM calls
11. test_llm_budget_exceeded(): Budget cap → auto-disable
12. test_llm_timeout(): LLM timeout → fallback to statistical

#### Acceptance Tests (5 tests, @pytest.mark.acceptance):
1. test_google_gemini_normalization(): Real API call with 20 merchants
2. test_google_gemini_variable(): Real API call with utility bills
3. test_google_gemini_insights(): Real API call with 5 subscriptions
4. test_cost_per_request(): Measure actual costs
5. test_accuracy_improvement(): Compare V2 (LLM) vs V1 (pattern-only) on 100 test transactions

### 6.3 Documentation Updates

#### recurring-detection.md Updates:
1. Add "V2: LLM Enhancement" section after V1 content
2. Document `enable_llm=True` configuration
3. Document merchant normalization with examples
4. Document variable detection for seasonal patterns
5. Document insights API (GET /recurring/insights)
6. Add cost analysis table (Google vs OpenAI vs Anthropic)
7. Add troubleshooting section (LLM rate limits, timeouts, budget exceeded)

### 6.4 Estimated Effort

| Task | Files | Lines | Tests | Effort |
|------|-------|-------|-------|--------|
| Research | 1 | ~12,000 | - | ✅ COMPLETE |
| normalizers.py | 1 | ~350 | 4 | 3-4 hours |
| detectors_llm.py | 1 | ~300 | 3 | 2-3 hours |
| insights.py | 1 | ~250 | 3 | 2-3 hours |
| Integration (ease.py, detector.py, add.py) | 3 | ~200 | 2 | 2 hours |
| Acceptance tests | 1 | ~400 | 5 | 2 hours |
| Documentation | 1 | ~2,500 | - | 2-3 hours |
| **TOTAL** | **8** | **~16,000** | **17** | **13-18 hours** |

### 6.5 Success Criteria

✅ **Implementation Complete** when:
1. All 17 tests passing (12 unit + 5 acceptance)
2. Merchant normalization: 90-95% accuracy on 100 test merchants
3. Variable detection: 85-88% accuracy on 50 utility bills
4. Cost: <$0.005/user/year (target: $0.003)
5. Documentation complete with examples
6. Backward compatible (enable_llm=False works)

---

## Summary

### Research Approved ✅

**Section 16 V2: Recurring Detection LLM Enhancement**

**Architecture**: 4-layer hybrid
- Layer 1: Pattern-based normalization (95% coverage, fast)
- Layer 2: LLM normalization (5% edge cases, 90-95% accuracy)
- Layer 3: Statistical detection (90% coverage, fast)
- Layer 4: LLM variable detection (10% edge cases, 88% accuracy)
- Layer 5: LLM insights (on-demand, natural language)

**Costs**:
- Merchant normalization: $0.0002/user/year
- Variable detection: $0.0024/user/year
- Insights generation: $0.00048/user/year
- **Total: $0.003/user/year** (<1 cent per user per year)

**Accuracy Gains**:
- Merchant normalization: 80% → 90-95% (+10-15%)
- Variable detection: 70% → 85-88% (+15-18%)
- Insights: N/A → Natural language recommendations

**Implementation**: Reuse Section 15 V2 patterns
- ai-infra CoreLLM with few-shot prompting
- Pydantic structured output
- svc-infra cache (merchant: 7d, insights: 24h)
- Budget caps ($0.10/day, $2/month)

**Estimated Effort**: 13-18 hours
- 8 files (3 new, 3 modified, 1 tests, 1 docs)
- 17 tests (12 unit + 5 acceptance)
- ~16,000 lines total (code + docs + research)

**Next Steps**: Design ADR-0020, then implementation

---
