# LLM API Pattern: achat vs with_structured_output

**Date**: 2025-11-07  
**Status**: Architecture Decision

---

## TL;DR

**Use `achat(output_schema=...)` for**:
- ✅ Single-shot inference with predictable structure
- ✅ Data transformation (categorization, normalization, parsing)
- ✅ Analysis with fixed output format (insights, reports)

**Use `achat()` (NO schema) for**:
- ✅ Multi-turn conversation (flexible, natural dialogue)
- ✅ Creative generation (variable format)
- ✅ When rigid structure hurts UX

---

## Pattern Comparison

### Pattern 1: `achat(output_schema=...)` ✅ CORRECT for Single-Shot

**Use Cases**:
- Transaction categorization
- Merchant normalization
- Financial insights generation
- Goal validation

**Example**:
```python
# Categorization: merchant → category (predictable structure)
from ai_infra.llm import CoreLLM

llm = CoreLLM()
response = await llm.achat(
    user_msg="Categorize: STARBUCKS",
    system=SYSTEM_PROMPT,
    provider="google",
    model_name="gemini-2.0-flash-exp",
    output_schema=CategoryPrediction,  # ✅ Forces JSON schema
    output_method="prompt",
)

# Result: CategoryPrediction(category="Coffee & Cafes", confidence=0.95, reasoning="...")
```

**Why This Works**:
- Same input always needs same output structure
- No conversation context
- Predictable workflow
- Need reliable parsing

---

### Pattern 2: `with_structured_output().ainvoke()` ✅ CORRECT for Single-Shot

**Use Cases**:
- Net worth insights
- Debt reduction plans
- Asset allocation advice
- Goal progress reports

**Example**:
```python
# Insights: snapshots → structured analysis (predictable structure)
from ai_infra.llm import CoreLLM

llm = CoreLLM()
structured = llm.with_structured_output(
    provider="google",
    model_name="gemini-2.0-flash-exp",
    schema=WealthTrendAnalysis,  # ✅ Forces JSON schema
    method="json_mode",
)

messages = [
    {"role": "system", "content": WEALTH_TRENDS_SYSTEM_PROMPT},
    {"role": "user", "content": "Analyze: Net worth increased $15k..."}
]

result: WealthTrendAnalysis = await structured.ainvoke(messages)

# Result: WealthTrendAnalysis(
#     summary="Net worth increased 15%...",
#     key_findings=["Investment gains +$12k", "Savings +$3k"],
#     recommendations=["Maintain savings rate", "Rebalance if >80% stocks"],
#     confidence=0.92
# )
```

**Why This Works**:
- Single-shot: one input → one output
- No multi-turn context
- Need structured data for downstream processing
- Predictable schema every time

---

### Pattern 3: `achat()` (NO schema) ✅ CORRECT for Conversation

**Use Cases**:
- Multi-turn financial planning Q&A
- Interactive advice
- Flexible responses (sometimes short, sometimes detailed)
- Natural dialogue

**Example**:
```python
# Conversation: flexible, natural dialogue (NO forced structure)
from ai_infra.llm import CoreLLM

llm = CoreLLM()

# Build messages with conversation history
messages = [
    {"role": "system", "content": CONVERSATION_SYSTEM_PROMPT},
    {"role": "user", "content": "How can I save more money?"}
]

response_text = await llm.achat(
    user_msg=messages[-1]["content"],
    system=messages[0]["content"],
    provider="google",
    model_name="gemini-2.0-flash-exp",
    # ✅ NO output_schema - natural conversation
)

# Result: "Based on your $575k net worth and retirement goal of $2M by 2050, 
# you're saving 15% of income ($1,200/month). To accelerate: 
# (1) Increase 401k contribution by 2%..."
```

**Why This Works**:
- Multi-turn: context matters, responses vary
- Sometimes short answers, sometimes detailed
- Follow-up questions should feel natural
- Rigid JSON structure breaks conversational flow
- User doesn't see internal structure

---

## Why NOT Use Structured Output for Conversation?

### ❌ Problem with `achat(output_schema=ConversationResponse)`

```python
# ❌ WRONG: Forces rigid structure every time
response = await llm.achat(
    user_msg="How can I save more?",
    system=CONVERSATION_SYSTEM_PROMPT,
    provider="google",
    model_name="gemini-2.0-flash-exp",
    output_schema=ConversationResponse,  # ❌ Forces JSON every time
    output_method="prompt",
)

# Result: ALWAYS returns:
# {
#   "answer": "...",
#   "follow_up_questions": ["...", "...", "..."],
#   "confidence": 0.85,
#   "sources": ["..."]
# }
```

**Issues**:
1. **Unnatural**: Real conversations don't always have 3 follow-up questions
2. **Token Waste**: LLM must generate confidence/sources even when not needed
3. **Inflexible**: Can't adapt response format to context
4. **UX Hurt**: User sees rigid structure instead of natural dialogue

---

### ✅ Solution: Natural Conversation + Internal Parsing

```python
# ✅ CORRECT: Natural conversation, parse as needed
response_text = await llm.achat(
    user_msg="How can I save more?",
    system=CONVERSATION_SYSTEM_PROMPT,
    provider="google",
    model_name="gemini-2.0-flash-exp",
    # NO output_schema - natural text response
)

# Parse internally (but LLM doesn't know about this structure)
response = ConversationResponse(
    answer=response_text,
    follow_up_questions=[],  # Extract if present, otherwise empty
    confidence=0.85,  # Default for natural responses
    sources=extract_sources_from_context(context)
)
```

**Benefits**:
1. **Natural**: LLM responds conversationally
2. **Efficient**: No wasted tokens on forced structure
3. **Flexible**: Can adapt to context (short/long, detailed/simple)
4. **Better UX**: User gets natural dialogue

---

## Decision Matrix

| Use Case | Pattern | Reasoning |
|----------|---------|-----------|
| **Transaction Categorization** | `achat(output_schema=CategoryPrediction)` | Single-shot, predictable structure, same every time |
| **Merchant Normalization** | `achat(output_schema=MerchantNormalized)` | Single-shot, need reliable parsing |
| **Net Worth Insights** | `with_structured_output(WealthTrendAnalysis).ainvoke()` | Single-shot, structured data for downstream |
| **Goal Validation** | `with_structured_output(GoalValidation).ainvoke()` | Single-shot, need predictable schema |
| **Financial Conversation** | `achat()` (NO schema) | Multi-turn, flexible format, natural dialogue |
| **Subscription Insights** | `achat(output_schema=SubscriptionInsights)` | Single-shot, fixed output format |
| **Variable Pattern Detection** | `achat(output_schema=VariableRecurringPattern)` | Single-shot, boolean result needed |

---

## Implementation Guidelines

### For Single-Shot Inference (Structured Output)

```python
# Option 1: achat with output_schema (categorization, normalization)
response = await llm.achat(
    user_msg="...",
    system="...",
    provider="google",
    model_name="gemini-2.0-flash-exp",
    output_schema=YourSchema,  # ✅ Pydantic model
    output_method="prompt",  # Most reliable
)

# Option 2: with_structured_output (insights, analysis)
structured = llm.with_structured_output(
    provider="google",
    model_name="gemini-2.0-flash-exp",
    schema=YourSchema,  # ✅ Pydantic model
    method="json_mode",
)
result = await structured.ainvoke(messages)
```

### For Conversation (Natural Dialogue)

```python
# Natural conversation (NO schema)
response_text = await llm.achat(
    user_msg="...",
    system="...",
    provider="google",
    model_name="gemini-2.0-flash-exp",
    # ✅ NO output_schema
)

# Parse internally if needed (but LLM doesn't know)
parsed = parse_response_if_needed(response_text, context)
```

---

## Summary

**Key Principle**: Match the API pattern to the use case.

- **Predictable structure?** → Use structured output (`achat(output_schema=...)` or `with_structured_output()`)
- **Flexible conversation?** → Use natural dialogue (`achat()` without schema)

**Current Implementation**:
- ✅ Categorization: `achat(output_schema=CategoryPrediction)` ✅ CORRECT
- ✅ Insights: `with_structured_output(WealthTrendAnalysis).ainvoke()` ✅ CORRECT
- ✅ Goals: `with_structured_output(GoalValidation).ainvoke()` ✅ CORRECT
- ✅ **Conversation**: `achat()` (NO schema) ✅ **NOW CORRECT** (fixed from `with_structured_output`)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-07  
**Related**: ADR-0021 (Net Worth LLM Insights), conversation-architecture-audit.md
