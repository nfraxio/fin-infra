# Net Worth LLM Insights Research (Section 17 V2)

**Date**: 2025-11-07  
**Status**: Research Complete  
**Classification**: Type A (Financial-specific domain logic using general AI infrastructure)

## Executive Summary

Section 17 V2 enhances net worth tracking with LLM-generated financial insights, multi-turn conversation for planning, and goal tracking with validation. This research confirms:

1. **ai-infra reuse**: ✅ CoreLLM provides structured output with Pydantic schemas, few-shot prompting, and multi-provider support
2. **svc-infra reuse**: ✅ Cache (24h TTL for insights), jobs (weekly goal check-ins), webhooks (goal progress alerts)
3. **fin-infra scope**: Financial-specific prompts, domain models, and validation logic
4. **Cost target**: <$0.10/user/month with caching (insights $0.06, conversation $0.02, goals $0.02)

## 1. ai-infra Check: Structured Output Capabilities

### 1.1 CoreLLM with Structured Output ✅ CONFIRMED

**Source**: `ai-infra/src/ai_infra/llm/core.py`, `ai-infra/src/ai_infra/llm/utils/structured.py`

**Available**:
```python
from ai_infra.llm import CoreLLM
from pydantic import BaseModel, Field

class FinancialInsight(BaseModel):
    summary: str = Field(..., description="1-2 sentence summary")
    key_findings: list[str] = Field(..., description="3-5 key findings")
    recommendations: list[str] = Field(..., description="Actionable recommendations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

llm = CoreLLM()
structured = llm.with_structured_output(
    provider="google",  # or "openai", "anthropic"
    model_name="gemini-2.0-flash-exp",
    schema=FinancialInsight,
    method="json_mode"  # or "json_schema", "function_calling"
)
result: FinancialInsight = structured.invoke([
    {"role": "user", "content": "Analyze my net worth trend..."}
])
```

**Features**:
- ✅ Pydantic schema validation (strict typing)
- ✅ Multi-provider support (Google, OpenAI, Anthropic)
- ✅ Fallback extraction (JSON fragments, error recovery)
- ✅ Method selection (json_mode, json_schema, function_calling)
- ✅ Automatic retry with `extra={"retry": {...}}`

**Providers Tested**:
- **Google Gemini**: `gemini-2.0-flash-exp` (default, cheapest: $0.00035/1K tokens)
- **OpenAI**: `gpt-4o-mini` ($0.0010/1K tokens)
- **Anthropic**: `claude-3-5-haiku-20241022` ($0.00080/1K tokens)

### 1.2 Few-Shot Prompting ✅ CONFIRMED

**Source**: `ai-infra/src/ai_infra/llm/utils/structured.py` (build_structured_messages)

**Pattern**:
```python
def build_structured_messages(
    schema: Type[BaseModel],
    user_msg: str,
    system_preamble: str | None = None,  # Few-shot examples go here
    forbid_prose: bool = True,
)
```

**Financial Insight Examples** (for system_preamble):
```
Example 1 (Wealth Trend):
User: Net worth increased from $500k to $575k over 6 months
Response: {
  "summary": "Net worth grew 15% ($75k) in 6 months, driven by market gains.",
  "key_findings": [
    "Investment portfolio up $60k (strong market performance)",
    "Salary increase added $20k to savings",
    "New mortgage reduced net worth by $5k"
  ],
  "recommendations": [
    "Maintain current savings rate (20% of income)",
    "Rebalance portfolio if equity allocation exceeds 80%",
    "Consider refinancing mortgage if rates drop below 5%"
  ],
  "confidence": 0.92
}

Example 2 (Debt Reduction):
User: $5k credit card (22% APR), $40k student loans (4% APR)
Response: {
  "summary": "Prioritize credit card payoff to save $1,100/year in interest.",
  "key_findings": [
    "Credit card costs $1,100/year vs student loan $1,600/year",
    "Credit card APR is 5.5x higher than student loans",
    "Paying off credit card first saves $1,100 in year 1"
  ],
  "recommendations": [
    "Pay $500/month extra on credit card (paid off in 11 months)",
    "Make minimum payments on student loans ($350/month)",
    "After credit card payoff, redirect $500 to student loans"
  ],
  "confidence": 0.98
}
```

### 1.3 Classification: Type A ✅ CONFIRMED

**Reasoning**:
- **ai-infra scope**: General LLM infrastructure (CoreLLM, structured output, providers)
- **fin-infra scope**: Financial-specific prompts, domain models, validation logic
- **Example**: ai-infra provides CoreLLM; fin-infra provides FinancialInsight schema + few-shot examples

**Boundary**:
- ❌ DON'T duplicate: LLM inference, provider management, retry logic (use ai-infra)
- ✅ DO implement: Financial domain prompts, Pydantic schemas, validation rules

### 1.4 Reuse Plan ✅ CONFIRMED

**ai-infra reuse**:
- `CoreLLM` for LLM inference with structured output
- `Providers` enum for provider selection (Google, OpenAI, Anthropic)
- `Models` enum for model selection (gemini-2.0-flash-exp, gpt-4o-mini, etc.)
- Structured output utils (`build_structured_messages`, `coerce_structured_result`)
- Retry logic (built into CoreLLM with `extra={"retry": {...}}`)

**svc-infra reuse**:
- `svc_infra.cache` for insights caching (24h TTL, 95%+ hit rate target)
- `svc_infra.jobs` for weekly goal check-ins (scheduler.add_task with 604800s interval)
- `svc_infra.webhooks` for goal progress alerts (event: net_worth.goal_progress)
- `svc_infra.api.fastapi.dual.protected.user_router` for authenticated endpoints

**fin-infra implementation**:
- `net_worth/insights.py`: Financial-specific Pydantic schemas + few-shot prompts
- `net_worth/conversation.py`: Multi-turn context management + safety filters
- `net_worth/goals.py`: Goal validation logic + progress tracking

## 2. LLM-Generated Financial Insights

### 2.1 Wealth Trend Analysis

**Input**: Historical net worth snapshots (current + previous 3-12 months)

**Output Schema**:
```python
class WealthTrendAnalysis(BaseModel):
    summary: str = Field(..., description="1-2 sentence trend summary")
    period: str = Field(..., description="Time period analyzed (e.g., '6 months')")
    change_amount: float = Field(..., description="Net worth change in USD")
    change_percent: float = Field(..., description="Percentage change")
    primary_drivers: list[str] = Field(..., max_length=5, description="Top 5 drivers")
    risk_factors: list[str] = Field(..., max_length=3, description="Top 3 risks")
    confidence: float = Field(..., ge=0.0, le=1.0)
```

**Example**:
```json
{
  "summary": "Net worth increased 15% ($75k) over 6 months, driven primarily by investment gains and salary growth.",
  "period": "6 months",
  "change_amount": 75000.0,
  "change_percent": 0.15,
  "primary_drivers": [
    "Investment portfolio gains: +$60k (market rally in tech sector)",
    "Salary increase: +$20k (new job with 15% raise)",
    "Savings rate: 20% of income ($1,500/month average)",
    "Real estate appreciation: +$10k (estimated market value)",
    "Crypto holdings: +$5k (Bitcoin rally)"
  ],
  "risk_factors": [
    "High equity allocation (90% stocks) - vulnerable to market correction",
    "New mortgage: -$5k net worth impact (closing costs)",
    "Rising credit card balance: +$2k debt (watch spending)"
  ],
  "confidence": 0.92
}
```

**Prompt Template** (system_preamble):
```
You are a certified financial advisor analyzing wealth trends.
Given historical net worth data, identify drivers of change and risks.
Be specific with numbers. Cite percentage changes and dollar amounts.
Focus on actionable insights, not generic advice.
```

### 2.2 Debt Reduction Strategies

**Input**: All liabilities with balances, APRs, minimum payments

**Output Schema**:
```python
class DebtReductionPlan(BaseModel):
    summary: str = Field(..., description="1-2 sentence strategy overview")
    total_debt: float = Field(..., description="Total debt across all accounts")
    weighted_avg_apr: float = Field(..., description="Weighted average APR")
    payoff_order: list[DebtPayoffStep] = Field(..., description="Ordered payoff steps")
    estimated_interest_saved: float = Field(..., description="Interest saved vs minimum payments")
    estimated_payoff_months: int = Field(..., description="Months to debt-free")
    confidence: float = Field(..., ge=0.0, le=1.0)

class DebtPayoffStep(BaseModel):
    account_name: str
    balance: float
    apr: float
    monthly_payment: float  # Recommended (not minimum)
    payoff_months: int
    interest_paid: float
    reasoning: str
```

**Example**:
```json
{
  "summary": "Pay off $5k credit card first (22% APR) to save $1,100/year, then tackle student loans (4% APR).",
  "total_debt": 45000.0,
  "weighted_avg_apr": 0.062,
  "payoff_order": [
    {
      "account_name": "Chase Credit Card",
      "balance": 5000.0,
      "apr": 0.22,
      "monthly_payment": 500.0,
      "payoff_months": 11,
      "interest_paid": 605.0,
      "reasoning": "Highest APR (22%) - costs $1,100/year. Paying off first saves maximum interest."
    },
    {
      "account_name": "Federal Student Loans",
      "balance": 40000.0,
      "apr": 0.04,
      "monthly_payment": 850.0,  # $350 minimum + $500 from credit card payoff
      "payoff_months": 52,
      "interest_paid": 4320.0,
      "reasoning": "Low APR (4%) - pay minimum until credit card is gone, then accelerate."
    }
  ],
  "estimated_interest_saved": 2100.0,
  "estimated_payoff_months": 63,
  "confidence": 0.98
}
```

**Prompt Template**:
```
You are a debt counselor using the avalanche method (highest APR first).
Calculate interest costs for each debt. Prioritize by APR.
Show math: interest saved = (current plan interest) - (avalanche interest).
Be specific with monthly payment amounts and timelines.
```

### 2.3 Goal Recommendations

**Input**: Current net worth, user goals, historical growth rate

**Output Schema**:
```python
class GoalRecommendation(BaseModel):
    goal_type: str = Field(..., description="retirement|home_purchase|debt_free|wealth_milestone")
    target_amount: float
    target_date: str  # ISO date
    current_progress: float  # 0.0 to 1.0
    required_monthly_savings: float
    alternative_paths: list[AlternativePath] = Field(..., max_length=3)
    feasibility: str = Field(..., description="feasible|challenging|unrealistic")
    confidence: float = Field(..., ge=0.0, le=1.0)

class AlternativePath(BaseModel):
    description: str
    required_monthly_savings: float
    investment_return_required: float
    trade_offs: str
```

**Example**:
```json
{
  "goal_type": "retirement",
  "target_amount": 2000000.0,
  "target_date": "2050-01-01",
  "current_progress": 0.15,
  "required_monthly_savings": 1500.0,
  "alternative_paths": [
    {
      "description": "Increase investment returns from 7% to 9% (riskier portfolio)",
      "required_monthly_savings": 1200.0,
      "investment_return_required": 0.09,
      "trade_offs": "Higher volatility, 30% chance of 10%+ loss in any year"
    },
    {
      "description": "Delay retirement by 2 years to age 67",
      "required_monthly_savings": 1100.0,
      "investment_return_required": 0.07,
      "trade_offs": "Work 2 extra years, more compounding time"
    },
    {
      "description": "Reduce retirement target to $1.5M (75% of goal)",
      "required_monthly_savings": 1100.0,
      "investment_return_required": 0.07,
      "trade_offs": "Lower income in retirement ($60k/year vs $80k/year)"
    }
  ],
  "feasibility": "feasible",
  "confidence": 0.89
}
```

### 2.4 Asset Allocation Advice

**Input**: Current assets, age, risk tolerance, investment goals

**Output Schema**:
```python
class AssetAllocationAdvice(BaseModel):
    summary: str
    current_allocation: dict[str, float]  # category -> percentage
    recommended_allocation: dict[str, float]
    rebalancing_steps: list[str]
    expected_return: float  # Annual return estimate
    expected_volatility: float  # Standard deviation
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)
```

**Example**:
```json
{
  "summary": "Portfolio is 90% stocks (high risk). Rebalance to 70/30 stocks/bonds for age 35.",
  "current_allocation": {
    "stocks": 0.90,
    "bonds": 0.05,
    "cash": 0.05
  },
  "recommended_allocation": {
    "stocks": 0.70,
    "bonds": 0.25,
    "cash": 0.05
  },
  "rebalancing_steps": [
    "Sell $50k in stocks (diversified across holdings)",
    "Buy $40k in bond index funds (BND or similar)",
    "Keep $10k in high-yield savings (emergency fund)"
  ],
  "expected_return": 0.075,
  "expected_volatility": 0.12,
  "reasoning": "Rule of thumb: (100 - age) in stocks = 65% for age 35. Recommend 70% for moderate risk tolerance. Bonds reduce volatility from 18% to 12% while maintaining 7.5% expected return.",
  "confidence": 0.85
}
```

## 3. Multi-Turn Conversation for Financial Planning

### 3.1 Context Management

**Context Structure**:
```python
class ConversationContext(BaseModel):
    user_id: str
    session_id: str
    current_net_worth: float
    historical_snapshots: list[NetWorthSnapshot]  # Last 12 months
    goals: list[FinancialGoal]  # Active goals
    previous_exchanges: list[Exchange]  # Last 10 turns
    created_at: str  # ISO datetime
    expires_at: str  # ISO datetime (24h from created_at)

class Exchange(BaseModel):
    question: str
    answer: str
    timestamp: str
    tokens_used: int
```

**Storage**:
- **svc-infra.cache**: Store context with 24h TTL
- **Key format**: `fin_infra:conversation:{user_id}:{session_id}`
- **Max size**: 10 exchanges (approx 5K tokens), older exchanges dropped
- **Cost**: ~$0.001/conversation (10 turns × $0.0001/turn with context)

### 3.2 Follow-Up Questions

**Examples**:
1. **Initial**: "How can I save more money each month?"
   - **Answer**: "Based on your $60k net worth and $5k/month income, you're saving 15% ($750/month). To increase savings: (1) Reduce dining out from $400 to $200/month (+$200), (2) Cancel unused subscriptions ($50/month), (3) Refinance car loan from 8% to 5% (+$75/month). Total: +$325/month (21% savings rate)."
   - **Follow-up**: "How do I refinance my car loan?"

2. **Initial**: "Should I pay off my mortgage early?"
   - **Answer**: "Your mortgage is 4% APR. If you can earn >4% investing (historical S&P 500: 10%), keep the mortgage and invest. You'd gain 6% spread ($6k/year on $100k). However, if you value debt-free living, pay extra principal."
   - **Follow-up**: "What if the market crashes?"

3. **Initial**: "Is my retirement on track?"
   - **Answer**: "At $300k saved for retirement at age 35, you're ahead of schedule. To reach $2M by 65 with 7% returns, you need $1,200/month savings. You're currently saving $1,500/month. You're 25% ahead of target."
   - **Follow-up**: "Can I retire early at 60?"

### 3.3 Conversation Memory

**Implementation**:
```python
class FinancialPlanningConversation:
    def __init__(self, llm: CoreLLM, cache):
        self.llm = llm
        self.cache = cache
    
    async def ask(
        self,
        user_id: str,
        question: str,
        session_id: str | None = None,
    ) -> ConversationResponse:
        # Load or create context
        context = await self._load_context(user_id, session_id)
        
        # Build messages with history
        messages = self._build_messages(context, question)
        
        # Call LLM
        structured = self.llm.with_structured_output(
            provider="google",
            model_name="gemini-2.0-flash-exp",
            schema=ConversationResponse,
        )
        response = structured.invoke(messages)
        
        # Update context
        context.previous_exchanges.append(Exchange(
            question=question,
            answer=response.answer,
            timestamp=datetime.utcnow().isoformat(),
            tokens_used=response.tokens_used,
        ))
        
        # Store context (24h TTL)
        await self._save_context(context)
        
        return response
```

**Message Building**:
```python
def _build_messages(self, context: ConversationContext, question: str) -> list[dict]:
    system_msg = f"""You are a certified financial advisor.
    
Current user context:
- Net worth: ${context.current_net_worth:,.0f}
- Goals: {len(context.goals)} active goals
- Recent trend: {context.historical_snapshots[-1].change_percent:.1%} change

Previous conversation:
{self._format_history(context.previous_exchanges)}

Provide specific, actionable advice. Cite numbers from user's data.
If you don't have enough information, ask clarifying questions.
"""
    
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": question}
    ]
```

### 3.4 Safety Filters

**Detect Sensitive Questions**:
```python
SENSITIVE_PATTERNS = [
    r"\b(ssn|social security number)\b",
    r"\b(password|pin|access code)\b",
    r"\b(credit card number|cvv)\b",
    r"\b(bank account number|routing number)\b",
]

def is_sensitive(question: str) -> bool:
    lower = question.lower()
    return any(re.search(pattern, lower) for pattern in SENSITIVE_PATTERNS)
```

**Response**:
```json
{
  "answer": "I cannot help with sensitive information like SSN, passwords, or account numbers. For account security, contact your financial institution directly.",
  "follow_up_questions": [],
  "confidence": 1.0,
  "sources": []
}
```

### 3.5 Cost Analysis

**Per Conversation** (10 turns):
- Base message: ~500 tokens × $0.00035/1K = $0.000175
- Context (10 previous exchanges): ~2,000 tokens × $0.00035/1K = $0.0007
- **Total per turn**: ~$0.0009
- **Total per conversation**: ~$0.009 (10 turns)

**With Caching** (50% context reuse):
- Turn 1: $0.0009 (full context)
- Turns 2-10: $0.0005 (cached context)
- **Total**: $0.0009 + (9 × $0.0005) = $0.0054

**Monthly Cost** (2 conversations/user):
- $0.0054 × 2 = **$0.011/user/month**
- **Target**: <$0.10/user/month ✅ WITHIN BUDGET

## 4. Goal Tracking with LLM Validation

### 4.1 Goal Types

#### Retirement Goal
```python
class RetirementGoal(BaseModel):
    target_amount: float  # $2M
    target_age: int  # 65
    current_age: int  # 35
    current_savings: float  # $300k
    monthly_contribution: float  # $1,500
    expected_return: float = 0.07  # 7% annual
```

**Validation Calculation**:
```
years_to_retire = target_age - current_age = 65 - 35 = 30
future_value = current_savings × (1 + return)^years + monthly × (((1 + return)^years - 1) / return)
             = $300k × 1.07^30 + $1,500 × (((1.07^30 - 1) / 0.07))
             = $2.29M (exceeds $2M target ✓)
```

#### Home Purchase Goal
```python
class HomePurchaseGoal(BaseModel):
    home_price: float  # $500k
    down_payment_percent: float = 0.20  # 20%
    target_date: str  # "2027-06-01"
    current_savings: float  # $50k
    monthly_savings: float  # $2,000
```

**Validation**:
```
down_payment_needed = $500k × 0.20 = $100k
months_to_target = months_between(now, target_date) = 30
savings_by_target = $50k + ($2,000 × 30) = $110k ✓
feasible = True (exceeds down payment by $10k)
```

#### Debt-Free Goal
```python
class DebtFreeGoal(BaseModel):
    total_debt: float  # $45k
    target_date: str  # "2028-01-01"
    monthly_payment: float  # $1,200
    weighted_avg_apr: float  # 6.2%
```

**Validation**:
```
Using debt payoff calculator with snowball/avalanche method
months_to_payoff = calculate_payoff_months($45k, $1,200, 6.2%) = 42
target_months = months_between(now, "2028-01-01") = 36
feasible = False (need $1,400/month to hit target)
```

#### Wealth Milestone
```python
class WealthMilestone(BaseModel):
    target_net_worth: float  # $1M
    target_date: str  # "2030-01-01"
    current_net_worth: float  # $575k
    historical_growth_rate: float  # 0.15 annual
```

**Validation**:
```
years_to_target = years_between(now, "2030-01-01") = 5
projected_net_worth = $575k × (1.15^5) = $1.16M ✓
feasible = True (exceeds target by $160k)
```

### 4.2 Progress Tracking

**Weekly Check-In** (via svc-infra.jobs):
```python
async def check_goal_progress(user_id: str, goal_id: str):
    # Get current net worth
    current = await get_current_net_worth(user_id)
    
    # Get goal
    goal = await get_goal(goal_id)
    
    # Calculate progress
    progress = calculate_progress(goal, current)
    
    # Generate report with LLM
    report = await generate_progress_report(goal, progress)
    
    # If off-track, send webhook alert
    if progress.status == "off_track":
        await send_webhook(user_id, "goal.off_track", report)
```

**Progress Report Schema**:
```python
class GoalProgressReport(BaseModel):
    goal_id: str
    status: str = Field(..., description="on_track|ahead|behind|off_track")
    current_progress: float  # 0.0 to 1.0
    projected_completion: str  # ISO date
    variance_from_target: float  # Days ahead/behind
    recommendations: list[str]  # Course corrections if needed
    confidence: float = Field(..., ge=0.0, le=1.0)
```

**Example**:
```json
{
  "goal_id": "retire_2050",
  "status": "ahead",
  "current_progress": 0.62,
  "projected_completion": "2048-06-01",
  "variance_from_target": 548,  # 18 months ahead
  "recommendations": [
    "Consider increasing 401k to max ($23k/year) to accelerate further",
    "Rebalance portfolio to 70/30 stocks/bonds as you approach retirement",
    "Review social security benefits at age 62 vs 67 for early retirement option"
  ],
  "confidence": 0.91
}
```

### 4.3 Course Correction

**When Off-Track**:
```python
class CourseCorrectionPlan(BaseModel):
    current_shortfall: float  # Dollars or percentage
    required_adjustments: list[Adjustment]
    alternative_goals: list[AlternativeGoal]
    confidence: float = Field(..., ge=0.0, le=1.0)

class Adjustment(BaseModel):
    action: str
    impact: float  # Monthly savings increase or debt reduction
    difficulty: str = Field(..., description="easy|moderate|hard")
    timeline: str  # When to implement
```

**Example**:
```json
{
  "current_shortfall": 5000.0,
  "required_adjustments": [
    {
      "action": "Reduce dining out from $400 to $200/month",
      "impact": 200.0,
      "difficulty": "easy",
      "timeline": "Immediate"
    },
    {
      "action": "Cancel unused gym membership",
      "impact": 50.0,
      "difficulty": "easy",
      "timeline": "This month"
    },
    {
      "action": "Increase 401k contribution from 8% to 10%",
      "impact": 150.0,
      "difficulty": "moderate",
      "timeline": "Next payroll cycle"
    }
  ],
  "alternative_goals": [
    {
      "description": "Extend target date by 6 months",
      "new_target_date": "2028-07-01",
      "required_monthly_savings": 1100.0,
      "trade_offs": "Debt-free 6 months later"
    }
  ],
  "confidence": 0.87
}
```

## 5. Cost Projections

### 5.1 Google Gemini Pricing (Default)

**Model**: gemini-2.0-flash-exp  
**Cost**: $0.00035/1K input tokens, $0.0014/1K output tokens

**Insights Generation** (1/day with 24h cache):
- Input: 2K tokens (net worth data + prompt) = $0.0007
- Output: 500 tokens (insights JSON) = $0.0007
- **Total**: $0.0014/generation × 30 days = **$0.042/user/month**

**Conversation** (2/month):
- 10 turns × $0.0009/turn = $0.009/conversation
- **Total**: $0.009 × 2 = **$0.018/user/month**

**Goal Tracking** (weekly check-ins):
- Input: 1.5K tokens (goal + net worth + prompt) = $0.0005
- Output: 300 tokens (progress report) = $0.0004
- **Total**: $0.0009/week × 4 weeks = **$0.0036/user/month**

**Grand Total**: $0.042 + $0.018 + $0.0036 = **$0.064/user/month**  
**Target**: <$0.10/user/month ✅ WITHIN BUDGET (36% safety margin)

### 5.2 Alternative Providers

**OpenAI** (gpt-4o-mini):
- $0.0010/1K tokens (2.86× more expensive than Gemini)
- **Total**: $0.064 × 2.86 = **$0.183/user/month** ⚠️ OVER BUDGET

**Anthropic** (claude-3-5-haiku):
- $0.00080/1K tokens (2.29× more expensive than Gemini)
- **Total**: $0.064 × 2.29 = **$0.147/user/month** ⚠️ OVER BUDGET

**Recommendation**: Use Google Gemini as default, allow provider override for premium tiers

## 6. Reuse Plan Summary

### 6.1 ai-infra Reuse ✅

| Component | Usage | Example |
|-----------|-------|---------|
| CoreLLM | LLM inference | `CoreLLM().with_structured_output(...)` |
| Structured output | Pydantic validation | `schema=FinancialInsight` |
| Providers | Multi-provider | `provider="google"` or `"openai"` |
| Retry logic | Automatic retries | `extra={"retry": {"attempts": 3}}` |

### 6.2 svc-infra Reuse ✅

| Component | Usage | Example |
|-----------|-------|---------|
| Cache | Insights caching | `cache.set(key, insights, ttl=86400)` |
| Jobs | Weekly goal checks | `scheduler.add_task(check_goals, 604800)` |
| Webhooks | Goal alerts | `send_webhook("goal.off_track", data)` |
| User router | Auth endpoints | `user_router(prefix="/net-worth")` |

### 6.3 fin-infra Implementation ✅

| File | Purpose | Lines (est) |
|------|---------|-------------|
| net_worth/insights.py | Financial insights generator | ~400 |
| net_worth/conversation.py | Multi-turn Q&A | ~350 |
| net_worth/goals.py | Goal tracking + validation | ~450 |
| net_worth/add.py | FastAPI integration (update) | +150 |
| tests/unit/test_net_worth_insights.py | Unit tests | ~600 |
| docs/net-worth.md | Documentation (V2 update) | +500 |

**Total**: ~2,450 new lines

## 7. Next Steps

### Research Phase ✅ COMPLETE
- [x] ai-infra check: Structured output with Pydantic schemas
- [x] Few-shot prompting patterns
- [x] Classification: Type A (financial-specific domain logic)
- [x] Reuse plan: ai-infra (CoreLLM), svc-infra (cache/jobs/webhooks)

### Design Phase (Next)
- [ ] Create ADR-0021: LLM-enhanced net worth architecture
- [ ] Design 4-layer architecture (calculation → insights → goals → conversation)
- [ ] Update easy_net_worth signature (enable_llm parameter)

### Implementation Phase
- [ ] Implement net_worth/insights.py (financial insights generator)
- [ ] Implement net_worth/conversation.py (multi-turn Q&A)
- [ ] Implement net_worth/goals.py (goal tracking + validation)
- [ ] Update add_net_worth_tracking() (LLM endpoints)

### Testing Phase
- [ ] Unit tests with mocked CoreLLM
- [ ] Verify insights quality (manual review)
- [ ] Verify cost stays under budget (<$0.10/user/month)

### Documentation Phase
- [ ] Update docs/net-worth.md with V2 LLM section
- [ ] Add code examples (insights, conversation, goals)
- [ ] Add cost analysis and provider comparison

---

**Classification**: Type A (Financial-specific) ✅  
**Reuse**: ai-infra (CoreLLM), svc-infra (cache/jobs/webhooks) ✅  
**Cost**: <$0.10/user/month with Google Gemini ✅  
**Status**: Research Complete, Ready for Design ✅
