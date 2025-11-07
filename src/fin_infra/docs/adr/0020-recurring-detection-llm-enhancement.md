# ADR-0020: Recurring Transaction Detection LLM Enhancement (V2)

**Status**: Proposed  
**Date**: 2025-11-07  
**Authors**: AI Agent  
**Related**: ADR-0019 (V1 Pattern-Based Detection), Section 15 V2 (Categorization LLM)

---

## Context

### V1 Implementation (Pattern-Based)

Section 16 V1 provides recurring transaction detection using statistical pattern matching:

**Strengths**:
- ✅ Fast (25ms for 100 transactions)
- ✅ No API costs
- ✅ 85% coverage for fixed-amount subscriptions (Netflix, Spotify, gym)
- ✅ Works well for normal distributions

**Limitations**:
- ❌ Merchant normalization: 80% accuracy on edge cases (cryptic names: "SQ *", "TST*", "AMZN MKTP")
- ❌ Variable amount detection: 70% accuracy (fails on seasonal patterns, occasional spikes)
- ❌ No natural language insights (just structured data)

### User Problems

1. **Merchant Grouping**: Users have 5 transactions from "NFLX*SUB", "Netflix Inc", "NETFLIX.COM" - V1 sees 3 separate merchants
2. **Utility Bills**: Winter heating bills ($45, $52, $55) vs summer ($48, $50, $49) - V1 flags as "not recurring" due to variance
3. **Insights**: Users want "You're spending $65/month on streaming - save $30 by bundling" - V1 has no insights

### Opportunity

**Section 15 V2** successfully integrated LLM for transaction categorization:
- 95-97% accuracy (vs 90% V1)
- Cost: <$0.0002/txn with 90% caching
- Few-shot prompting with ai-infra CoreLLM

**Can we apply same pattern to recurring detection?**

---

## Decision

Implement **4-layer hybrid LLM enhancement** for recurring detection:

### Layer 1: Pattern-Based Merchant Normalization (Fast Path)
- **Method**: RapidFuzz fuzzy matching (V1)
- **Coverage**: 95% of merchants
- **Accuracy**: 80% on edge cases
- **Latency**: ~5ms
- **Cost**: $0

### Layer 2: LLM Merchant Normalization (Edge Cases)
- **Method**: Few-shot prompting with ai-infra CoreLLM
- **Coverage**: 5% of merchants (cryptic names)
- **Accuracy**: 90-95%
- **Latency**: ~200-400ms (uncached), <1ms (cached 95%)
- **Cost**: $0.000004/request (with 95% caching)
- **Output**: `MerchantNormalized(canonical_name, merchant_type, confidence, reasoning)`

### Layer 3: Statistical Pattern Detection (Normal Distributions)
- **Method**: Mean ± 2σ variance analysis (V1)
- **Coverage**: 90% of patterns
- **Accuracy**: 85% (fixed), 70% (variable <20% variance)
- **Latency**: ~20ms
- **Cost**: $0

### Layer 4: LLM Variable Detection (Seasonal/Spikes)
- **Method**: Few-shot prompting with ai-infra CoreLLM
- **Coverage**: 10% of patterns (20-40% variance)
- **Accuracy**: 88%
- **Latency**: ~200-400ms
- **Cost**: $0.00001/detection
- **Output**: `VariableRecurringPattern(is_recurring, cadence, expected_range, reasoning, confidence)`

### Layer 5: LLM Insights (Optional, On-Demand)
- **Method**: Few-shot prompting with ai-infra CoreLLM
- **Coverage**: User-initiated via GET /recurring/insights
- **Accuracy**: Qualitative (natural language)
- **Latency**: ~300-500ms (uncached), <1ms (cached 80%)
- **Cost**: $0.00004/generation (with 80% caching)
- **Output**: `SubscriptionInsights(summary, top_subscriptions, recommendations)`

---

## Architecture

### Data Flow

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

### Graceful Degradation

**LLM Disabled** (`enable_llm=False`):
- Use Layer 1 only (RapidFuzz)
- Use Layer 3 only (statistical)
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

---

## Pydantic Schemas

### MerchantNormalized (Layer 2 Output)

```python
class MerchantNormalized(BaseModel):
    """Result of LLM merchant name normalization."""
    
    canonical_name: str = Field(
        ..., 
        description="Canonical merchant name (e.g., 'Netflix' for 'NFLX*SUB')"
    )
    merchant_type: str = Field(
        ..., 
        description="Merchant category: streaming, coffee_shop, grocery, etc."
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score 0.0-1.0"
    )
    reasoning: str = Field(
        ..., 
        max_length=150, 
        description="Brief explanation of normalization"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "canonical_name": "Netflix",
                "merchant_type": "streaming",
                "confidence": 0.95,
                "reasoning": "NFLX is Netflix subscription prefix"
            }
        }
    )
```

### VariableRecurringPattern (Layer 4 Output)

```python
class VariableRecurringPattern(BaseModel):
    """Result of LLM variable amount detection."""
    
    is_recurring: bool = Field(
        ..., 
        description="True if pattern is recurring despite variance"
    )
    cadence: Optional[str] = Field(
        None, 
        description="Frequency: monthly, quarterly, annual, etc."
    )
    expected_range: Optional[tuple[float, float]] = Field(
        None, 
        description="Expected amount range (min, max)"
    )
    reasoning: str = Field(
        ..., 
        max_length=200, 
        description="Explanation of variance (seasonal, spikes, etc.)"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score 0.0-1.0"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_recurring": True,
                "cadence": "monthly",
                "expected_range": (45.0, 60.0),
                "reasoning": "Seasonal winter heating causes variance",
                "confidence": 0.85
            }
        }
    )
```

### SubscriptionInsights (Layer 5 Output)

```python
class SubscriptionInsights(BaseModel):
    """Natural language subscription insights."""
    
    summary: str = Field(
        ..., 
        max_length=500, 
        description="Overall subscription spending summary"
    )
    top_subscriptions: list[dict[str, Any]] = Field(
        ..., 
        max_items=5, 
        description="Top 5 subscriptions by cost"
    )
    recommendations: list[str] = Field(
        default_factory=list, 
        max_items=3, 
        description="Up to 3 cost-saving recommendations"
    )
    total_monthly_cost: float = Field(
        ..., 
        ge=0.0, 
        description="Total monthly subscription cost"
    )
    potential_savings: Optional[float] = Field(
        None, 
        ge=0.0, 
        description="Potential monthly savings from recommendations"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "summary": "You have 5 streaming subscriptions totaling $64.95/month.",
                "top_subscriptions": [
                    {"merchant": "Netflix", "amount": 15.99, "cadence": "monthly"},
                    {"merchant": "Spotify", "amount": 9.99, "cadence": "monthly"}
                ],
                "recommendations": [
                    "Consider Disney+ bundle to save $30/month",
                    "Cancel Hulu - unused for 3 months"
                ],
                "total_monthly_cost": 64.95,
                "potential_savings": 30.00
            }
        }
    )
```

---

## Few-Shot Prompt Templates

### Merchant Normalization Prompt

```python
MERCHANT_NORMALIZATION_SYSTEM_PROMPT = """
You are a financial transaction expert specializing in merchant name normalization.
Given a merchant name from a bank transaction, identify the canonical merchant name
and merchant type.

Common patterns:
- Payment processors: SQ * (Square), TST* (Toast), CLOVER* (Clover), STRIPE* (Stripe)
- Subscriptions: NFLX* (Netflix), SPFY* (Spotify), AMZN* (Amazon), AAPL* (Apple)
- Store numbers: Remove #1234, store-specific identifiers
- Legal entities: Remove Inc, LLC, Corp, Ltd
- POS systems: TST* (Toast), CLOVER*, SQUARE*

Examples:
1. "NFLX*SUB #12345" → Netflix (streaming)
2. "Netflix Inc" → Netflix (streaming)
3. "NETFLIX.COM" → Netflix (streaming)
4. "SQ *COZY CAFE" → Cozy Cafe (coffee_shop, Square processor)
5. "TST* STARBUCKS" → Starbucks (coffee_shop, Toast POS)
6. "AMZN MKTP US" → Amazon (online_shopping)
7. "SPFY*PREMIUM" → Spotify (streaming)
8. "UBER *TRIP 12345" → Uber (rideshare)
9. "LYFT   *RIDE ABC" → Lyft (rideshare)
10. "CLOVER* PIZZA PLACE" → Pizza Place (restaurant, Clover POS)
11. "AAPL* ICLOUD STORAGE" → Apple iCloud (cloud_storage)
12. "MSFT*MICROSOFT 365" → Microsoft 365 (software_subscription)
13. "DISNEY PLUS #123" → Disney Plus (streaming)
14. "PRIME VIDEO" → Amazon Prime Video (streaming)
15. "CITY ELECTRIC #456" → City Electric (utility_electric)
16. "T-MOBILE USA" → T-Mobile (phone_service)
17. "VERIZON WIRELESS" → Verizon (phone_service)
18. "WHOLE FOODS MKT #789" → Whole Foods (grocery)
19. "STARBUCKS #1234" → Starbucks (coffee_shop)
20. "LA FITNESS #567" → LA Fitness (gym)

Output format (JSON):
{
  "canonical_name": "Netflix",
  "merchant_type": "streaming",
  "confidence": 0.95,
  "reasoning": "NFLX is Netflix subscription prefix"
}
"""

MERCHANT_NORMALIZATION_USER_PROMPT = "Normalize this merchant name: {merchant_name}"
```

### Variable Amount Detection Prompt

```python
VARIABLE_DETECTION_SYSTEM_PROMPT = """
You are a financial analysis expert specializing in recurring payment detection.
Given a merchant name and transaction history, determine if the variable amounts
represent a recurring subscription or bill.

Common patterns:
- Utility bills: Seasonal variation (2x in winter for heating, summer for AC)
- Phone bills: Occasional spikes (overage charges, international calls)
- Gym fees: Annual fee waived, promotional discounts
- Streaming services: Price changes (rare, <5% variance)

Examples:
1. Merchant: "City Electric"
   Amounts: [$45, $52, $48, $55, $50, $49]
   Dates: Monthly (15th ±7 days)
   → is_recurring: true, cadence: "monthly", range: (40, 60), 
     reasoning: "Seasonal winter heating variation", confidence: 0.85

2. Merchant: "T-Mobile"
   Amounts: [$50, $50, $50, $78, $50, $50]
   Dates: Monthly (20th ±3 days)
   → is_recurring: true, cadence: "monthly", range: (50, 80),
     reasoning: "Occasional overage charge spike", confidence: 0.80

3. Merchant: "Random Store"
   Amounts: [$10, $45, $23, $67, $12]
   Dates: Irregular
   → is_recurring: false, reasoning: "Too much variance, no pattern", confidence: 0.95

4. Merchant: "Gas Company"
   Amounts: [$45, $48, $50, $52, $120, $115]
   Dates: Monthly
   → is_recurring: true, cadence: "monthly", range: (40, 120),
     reasoning: "Winter heating season doubles bill", confidence: 0.80

5. Merchant: "Gym Membership"
   Amounts: [$40, $40, $0, $40, $40]
   Dates: Monthly
   → is_recurring: true, cadence: "monthly", range: (0, 40),
     reasoning: "Annual fee waived one month", confidence: 0.75

Output format (JSON):
{
  "is_recurring": true,
  "cadence": "monthly",
  "expected_range": [45.0, 60.0],
  "reasoning": "Seasonal winter heating causes variance",
  "confidence": 0.85
}
"""

VARIABLE_DETECTION_USER_PROMPT = """
Merchant: {merchant_name}
Amounts: {amounts}
Dates: {date_pattern}

Is this a recurring pattern?
"""
```

### Insights Generation Prompt

```python
INSIGHTS_GENERATION_SYSTEM_PROMPT = """
You are a personal finance advisor specializing in subscription management.
Given a user's detected subscriptions, provide insights and recommendations
to help them save money and optimize their spending.

Guidelines:
- Be conversational and friendly
- Focus on actionable recommendations (bundle deals, unused subscriptions)
- Highlight potential savings with specific dollar amounts
- Limit to top 3 recommendations

Examples:
1. Subscriptions: Netflix $15.99, Hulu $12.99, Disney+ $10.99, Spotify $9.99, Amazon Prime $14.99
   → "You have 5 subscriptions totaling $64.95/month. Consider the Disney+ bundle 
      (Disney+, Hulu, ESPN+ for $19.99) to save $29.98/month. Also, Amazon Prime 
      includes Prime Video - you may be able to cancel Netflix or Hulu."

2. Subscriptions: Spotify $9.99, Apple Music $10.99
   → "You're paying for both Spotify and Apple Music ($20.98/month). Cancel one 
      to save $10.99/month."

3. Subscriptions: LA Fitness $40, Planet Fitness $10
   → "You have 2 gym memberships totaling $50/month. Consider consolidating to 
      just Planet Fitness to save $40/month."

Output format (JSON):
{
  "summary": "You have 5 streaming subscriptions totaling $64.95/month.",
  "top_subscriptions": [
    {"merchant": "Netflix", "amount": 15.99, "cadence": "monthly"},
    {"merchant": "Hulu", "amount": 12.99, "cadence": "monthly"}
  ],
  "recommendations": [
    "Consider Disney+ bundle to save $30/month",
    "Amazon Prime includes Prime Video - cancel Netflix/Hulu"
  ],
  "total_monthly_cost": 64.95,
  "potential_savings": 30.00
}
"""

INSIGHTS_GENERATION_USER_PROMPT = """
User's subscriptions:
{subscriptions_json}

Provide insights and recommendations.
"""
```

---

## Cost Analysis

### Per-Request Costs (Google Gemini 2.0 Flash)

| Use Case | Input Tokens | Output Tokens | Cost/Request | With Caching | Effective Cost |
|----------|--------------|---------------|--------------|--------------|----------------|
| Merchant Normalization | 850 | 50 | $0.00008 | 95% hit (7d TTL) | $0.000004 |
| Variable Detection | 1,000 | 100 | $0.0001 | N/A (run once) | $0.0001 |
| Insights Generation | 1,300 | 200 | $0.0002 | 80% hit (24h TTL) | $0.00004 |

### Annual Cost Per User

| Use Case | Frequency | Cost/Request | Annual Cost |
|----------|-----------|--------------|-------------|
| Merchant Normalization | 50 unique merchants | $0.000004 | **$0.0002** |
| Variable Detection | 2 patterns × 12 checks | $0.0001 | **$0.0024** |
| Insights Generation | 12 generations × 20% miss | $0.0002 | **$0.00048** |
| **TOTAL** | | | **$0.00288** |

**Rounded Total**: ~$0.003/user/year (<1 cent per user per year)

### At Scale

- 1,000 users: **$3/year**
- 10,000 users: **$30/year**
- 100,000 users: **$300/year**
- 1,000,000 users: **$3,000/year**

### Budget Caps

**Daily Budget**: $0.10/day
- Supports ~33,000 merchant normalizations/day
- Or ~1,000 variable detections/day
- Sufficient for 100k+ users

**Monthly Budget**: $2.00/month
- Supports ~700k users at $0.003/user/year
- Safety margin: 10x expected usage

---

## Implementation Plan

### New Files (3)

#### 1. `recurring/normalizers.py`
```python
"""
LLM-based merchant name normalization.

Handles cryptic merchant names (SQ *, TST*, AMZN MKTP) using
ai-infra CoreLLM with few-shot prompting.
"""

from ai_infra.llm import CoreLLM
from pydantic import BaseModel, Field, ConfigDict

class MerchantNormalized(BaseModel):
    """LLM merchant normalization result."""
    canonical_name: str
    merchant_type: str
    confidence: float
    reasoning: str

class MerchantNormalizer:
    """LLM merchant name normalizer with caching."""
    
    def __init__(
        self,
        provider: str = "google",
        model_name: str = "gemini-2.0-flash-exp",
        cache_ttl: int = 604800,  # 7 days
        enable_cache: bool = True,
    ):
        self.llm = CoreLLM()
        self.provider = provider
        self.model_name = model_name
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache
    
    async def normalize(
        self, 
        merchant_name: str
    ) -> MerchantNormalized:
        """
        Normalize merchant name using LLM.
        
        1. Check cache first (95% hit rate)
        2. Call CoreLLM if cache miss
        3. Cache result (7-day TTL)
        4. Return MerchantNormalized
        """
        # Implementation in next step
        pass
```

#### 2. `recurring/detectors_llm.py`
```python
"""
LLM-based variable amount detection for seasonal patterns.

Handles edge cases where statistical methods fail:
- Utility bills with seasonal variation (winter heating spikes)
- Phone bills with occasional overage charges
- Gym fees with promotional discounts
"""

from ai_infra.llm import CoreLLM
from pydantic import BaseModel, Field, ConfigDict

class VariableRecurringPattern(BaseModel):
    """LLM variable amount detection result."""
    is_recurring: bool
    cadence: Optional[str]
    expected_range: Optional[tuple[float, float]]
    reasoning: str
    confidence: float

class VariableDetectorLLM:
    """LLM variable amount detector."""
    
    def __init__(
        self,
        provider: str = "google",
        model_name: str = "gemini-2.0-flash-exp",
    ):
        self.llm = CoreLLM()
        self.provider = provider
        self.model_name = model_name
    
    async def detect(
        self,
        merchant_name: str,
        amounts: list[float],
        date_pattern: str,
    ) -> VariableRecurringPattern:
        """
        Detect variable recurring pattern using LLM.
        
        Only called when variance is 20-40% (ambiguous).
        """
        # Implementation in next step
        pass
```

#### 3. `recurring/insights.py`
```python
"""
Natural language subscription insights generation.

Provides:
- Monthly spending summary
- Top subscriptions by cost
- Cost-saving recommendations (bundle deals, unused subscriptions)
"""

from ai_infra.llm import CoreLLM
from pydantic import BaseModel, Field, ConfigDict

class SubscriptionInsights(BaseModel):
    """LLM-generated subscription insights."""
    summary: str
    top_subscriptions: list[dict[str, Any]]
    recommendations: list[str]
    total_monthly_cost: float
    potential_savings: Optional[float]

class SubscriptionInsightsGenerator:
    """LLM insights generator with caching."""
    
    def __init__(
        self,
        provider: str = "google",
        model_name: str = "gemini-2.0-flash-exp",
        cache_ttl: int = 86400,  # 24 hours
    ):
        self.llm = CoreLLM()
        self.provider = provider
        self.model_name = model_name
        self.cache_ttl = cache_ttl
    
    async def generate(
        self,
        subscriptions: list[dict[str, Any]]
    ) -> SubscriptionInsights:
        """
        Generate subscription insights.
        
        1. Check cache first (80% hit rate)
        2. Call CoreLLM if cache miss
        3. Cache result (24h TTL)
        4. Return SubscriptionInsights
        """
        # Implementation in next step
        pass
```

### Modified Files (3)

#### 1. `recurring/ease.py`
```python
def easy_recurring_detection(
    min_occurrences: int = 3,
    amount_tolerance: float = 0.02,
    date_tolerance_days: int = 7,
    enable_ml: bool = False,
    enable_llm: bool = False,  # NEW: LLM enhancement
    llm_provider: str = "google",  # NEW: Google Gemini default
    llm_model: Optional[str] = None,  # NEW: Model override
    llm_confidence_threshold: float = 0.8,  # NEW: When to trigger LLM
    llm_cache_merchant_ttl: int = 604800,  # NEW: 7 days
    llm_cache_insights_ttl: int = 86400,  # NEW: 24 hours
    llm_max_cost_per_day: float = 0.10,  # NEW: Budget cap
    llm_max_cost_per_month: float = 2.00,  # NEW: Budget cap
    **config,
) -> RecurringDetector:
    """
    Create configured recurring transaction detector.
    
    V2 Parameters (LLM Enhancement):
        enable_llm: Enable LLM for merchant normalization and variable detection
        llm_provider: "google", "openai", "anthropic"
        llm_model: Model override (default: gemini-2.0-flash-exp)
        llm_confidence_threshold: Trigger LLM when RapidFuzz < threshold
        llm_cache_merchant_ttl: Merchant normalization cache TTL (7 days)
        llm_cache_insights_ttl: Insights cache TTL (24 hours)
        llm_max_cost_per_day: Daily budget cap ($0.10 default)
        llm_max_cost_per_month: Monthly budget cap ($2.00 default)
    """
    # Initialize MerchantNormalizer if LLM enabled
    # Initialize VariableDetectorLLM if LLM enabled
    # Pass to RecurringDetector
    pass
```

#### 2. `recurring/detector.py`
```python
class RecurringDetector:
    def __init__(
        self,
        min_occurrences: int = 3,
        amount_tolerance: float = 0.02,
        date_tolerance_days: int = 7,
        merchant_normalizer: Optional[MerchantNormalizer] = None,  # NEW
        variable_detector_llm: Optional[VariableDetectorLLM] = None,  # NEW
    ):
        self.min_occurrences = min_occurrences
        self.amount_tolerance = amount_tolerance
        self.date_tolerance_days = date_tolerance_days
        self.merchant_normalizer = merchant_normalizer
        self.variable_detector_llm = variable_detector_llm
    
    async def detect_patterns(
        self, 
        transactions: list[dict[str, Any]]
    ) -> list[RecurringPattern]:
        """
        Detect recurring patterns with optional LLM enhancement.
        
        Layer 1: RapidFuzz merchant normalization
        Layer 2: LLM merchant normalization (if confidence < 0.8)
        Layer 3: Statistical pattern detection
        Layer 4: LLM variable detection (if variance 20-40%)
        """
        # Integration logic in next step
        pass
```

#### 3. `recurring/add.py`
```python
def add_recurring_detection(
    app: FastAPI,
    prefix: str = "/recurring",
    enable_llm: bool = False,  # NEW
    **config,
) -> RecurringDetector:
    """
    Add recurring detection endpoints to FastAPI app.
    
    V2 Endpoints:
        GET /recurring/insights - LLM-generated insights (NEW)
    """
    # Add new insights endpoint
    @router.get("/insights")
    async def get_insights(user_id: str) -> SubscriptionInsights:
        """Get LLM-generated subscription insights."""
        # Implementation in next step
        pass
```

---

## Consequences

### Positive

✅ **Better Merchant Grouping**: 90-95% accuracy (vs 80% V1) on cryptic names  
✅ **Seasonal Detection**: 88% accuracy (vs 70% V1) for utility bills  
✅ **Natural Language Insights**: Actionable recommendations to save money  
✅ **Cost-Effective**: ~$0.003/user/year (less than 1 cent)  
✅ **Backward Compatible**: LLM optional via `enable_llm=False`  
✅ **Graceful Degradation**: Fallback to V1 if LLM fails or budget exceeded  

### Negative

⚠️ **Added Complexity**: 3 new files, 6 new parameters, LLM error handling  
⚠️ **Latency**: 200-400ms for uncached LLM calls (vs <50ms V1)  
⚠️ **API Dependency**: Requires ai-infra and LLM provider API keys  
⚠️ **Budget Monitoring**: Need to track daily/monthly costs  

### Mitigations

✅ **Caching**: 95% hit rate (merchants), 80% hit rate (insights) → most requests <1ms  
✅ **Budget Caps**: Auto-disable at $0.10/day, $2/month  
✅ **Fallback**: V1 behavior if LLM disabled/failed  
✅ **Documentation**: Clear setup guide, cost estimates, troubleshooting  

---

## Alternatives Considered

### Alternative 1: LLM-Only (No Hybrid)
**Rejected**: Too expensive ($0.0001/merchant vs $0.000004 hybrid), slower

### Alternative 2: Fine-Tuning Instead of Few-Shot
**Rejected**: Overkill (95-98% vs 90-95%), high complexity, maintenance overhead

### Alternative 3: External Service (Plaid Insights API)
**Rejected**: $0.01/user/month (3x more expensive), vendor lock-in, less customization

### Alternative 4: No LLM Enhancement (V1 Only)
**Rejected**: 80% merchant accuracy insufficient, 70% variable detection misses seasonal patterns, no insights

---

## Success Metrics

### Accuracy Targets

| Metric | V1 Baseline | V2 Target | Measurement |
|--------|-------------|-----------|-------------|
| Merchant Normalization | 80% | **90-95%** | 100 test merchant variants |
| Variable Detection | 70% | **85-88%** | 50 utility bill patterns |
| Overall Detection | 85% | **92%+** | 150 labeled transaction histories |
| False Positive Rate | <5% | **<3%** | Random transaction noise |

### Cost Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cost per User per Year | <$0.005 | Monthly tracking |
| Merchant Cache Hit Rate | >90% | Cache metrics |
| Insights Cache Hit Rate | >75% | Cache metrics |
| Budget Overruns | 0 | Alert on exceeds |

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| P50 Latency (cached) | <5ms | Same as V1 |
| P99 Latency (uncached) | <500ms | LLM calls |
| Throughput | >1,000 txns/sec | Load testing |

---

## References

- ADR-0019: Recurring Transaction Detection V1 (Pattern-Based)
- Section 15 V2: Transaction Categorization LLM Enhancement
- Research: `recurring-detection-llm-research.md` (12,000 lines)
- ai-infra CoreLLM API Documentation
- svc-infra Cache Integration Guide

---

**Status**: Ready for Implementation  
**Next Step**: Implement `normalizers.py`, `detectors_llm.py`, `insights.py`
