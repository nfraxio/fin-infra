# ADR-0018: Transaction Categorization Architecture

**Date**: November 6, 2025  
**Status**: Accepted  
**Deciders**: Engineering Team  
**Related**: Section 15 (Transaction Categorization)

## Context

Financial applications need to automatically categorize transactions (e.g., "Starbucks #1234" → "Coffee Shops") to enable budgeting, spending analysis, and financial insights. Users expect high accuracy (95%+), fast response times (<100ms), and the ability to override incorrect predictions.

### Requirements

1. **High Accuracy**: 95%+ correct predictions for known merchants
2. **Fast Cold Start**: Ship with pre-trained model (no initial training period)
3. **Handles Variants**: "STARBUCKS #1234" and "Starbucks Store 5678" → same category
4. **User Overrides**: Users can correct predictions and create custom categories
5. **Self-Improving**: Accuracy increases as users correct predictions
6. **Resource Efficient**: No GPU required, model size <20MB
7. **Explainable**: Users understand why a transaction was categorized

### Constraints

- **No ML Infrastructure in svc-infra**: Confirmed via codebase search (0 matches for sklearn/tensorflow/pytorch)
- **Small Model Size**: Must bundle model in package (<20MB to keep package lightweight)
- **No External API Dependencies**: Avoid costs and latency of Plaid Entity API ($0.01/lookup)
- **Deterministic for Known Merchants**: Same merchant → same category (user trust)

## Decision

We will implement a **hybrid approach** with three layers:

### Layer 1: Rule-Based (Primary, 85-90% coverage)

**Exact Dictionary Lookup** (O(1))
```python
MERCHANT_RULES = {
    "starbucks": "Coffee Shops",
    "shell": "Gas Stations",
    "netflix": "Streaming Services",
    # ... 50,000+ entries
}
```

**Pros**:
- Deterministic (same merchant → same category)
- Fast (O(1) dictionary lookup)
- Ships with 50k+ pre-defined rules
- 100% accuracy for known merchants

**Coverage**: 85-90% of transactions (known merchants)

### Layer 2: Pattern Matching (5-10% coverage)

**Regex Patterns** (O(n), n ≈ 1,000 patterns)
```python
CATEGORY_PATTERNS = [
    (re.compile(r"(?i)starbucks|dunkin|peet'?s"), "Coffee Shops"),
    (re.compile(r"(?i)shell|chevron|mobil|exxon"), "Gas Stations"),
    (re.compile(r"(?i)netflix|hulu|spotify|disney\+"), "Streaming Services"),
    # ... 1,000+ patterns
]
```

**Pros**:
- Handles variants ("STARBUCKS #1234", "Starbucks Store 5678")
- Fast (O(n), but n is small ~1,000)
- Still deterministic and explainable

**Coverage**: 5-10% of transactions (known chains with variants)

### Layer 3: ML Fallback (5% coverage, unknown merchants)

**sklearn Naive Bayes** (O(features × classes))
```python
model = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
    ('clf', MultinomialNB(alpha=0.1)),
])
```

**Training Data**: 100k+ transactions from Plaid public dataset  
**Model Size**: ~5MB (TF-IDF vectors + Naive Bayes weights)  
**Inference Speed**: 1000 predictions/sec (CPU)  

**Pros**:
- Handles completely unknown merchants
- Provides confidence scores (can show top-3 predictions)
- Improves with active learning (user corrections)

**Coverage**: 5% of transactions (unknown merchants)

### Overall Flow

```python
def categorize_transaction(merchant_name: str) -> tuple[str, float]:
    # Layer 1: Exact match (O(1))
    normalized = normalize_merchant(merchant_name)
    if normalized in MERCHANT_RULES:
        return MERCHANT_RULES[normalized], 1.0
    
    # Layer 2: Regex patterns (O(n), n=1000)
    for pattern, category in CATEGORY_PATTERNS:
        if pattern.match(normalized):
            return category, 0.95
    
    # Layer 3: ML fallback
    prediction = ml_model.predict_proba([normalized])[0]
    category = ml_model.classes_[prediction.argmax()]
    confidence = prediction.max()
    
    # Flag low-confidence predictions for user review
    if confidence < 0.75:
        flag_for_user_review(merchant_name, category, confidence)
    
    return category, confidence
```

**Expected Accuracy**:
- Layer 1: 100% (known merchants, 85-90% coverage)
- Layer 2: 98% (regex patterns, 5-10% coverage)
- Layer 3: 85% (ML fallback, 5% coverage)
- **Overall**: 96-98% accuracy

## Alternatives Considered

### Alternative 1: Pure Rule-Based (YNAB Approach)

**Rejected** because it cannot handle unknown merchants or variants without manual rule updates.

**Example**: "Joe's Coffee Shop" (unknown merchant) → Uncategorized (poor user experience)

### Alternative 2: Pure ML (Research-First Approach)

**Rejected** because it requires large training dataset (100k+ transactions) before shipping, lacks explainability, and is not deterministic.

**Example**: Model update changes "Starbucks" prediction from "Coffee Shops" to "Food & Dining" (user confusion)

### Alternative 3: External API (Plaid Entity)

**Rejected** because of cost ($0.01/lookup = $10k/month for 1M transactions) and latency (100-200ms per API call).

### Alternative 4: BERT / Transformers

**Rejected** because of model size (500MB), slow inference (10-50 pred/sec), and overkill complexity for merchant name classification.

## Category Taxonomy

We will use an **MX-style taxonomy** with 50-60 top-level categories:

### Core Categories (50-60)

```python
CATEGORIES = [
    # Income
    "Paycheck", "Investment Income", "Interest Income", "Other Income",
    
    # Fixed Expenses
    "Rent/Mortgage", "Utilities", "Insurance", "Loan Payments",
    
    # Variable Expenses
    "Groceries", "Restaurants", "Coffee Shops", "Fast Food",
    "Gas Stations", "Parking", "Public Transportation", "Ride Share",
    "Shopping", "Clothing", "Electronics", "Home Improvement",
    "Entertainment", "Streaming Services", "Movies", "Concerts",
    "Healthcare", "Pharmacy", "Doctor", "Gym/Fitness",
    "Travel", "Hotels", "Flights", "Vacation",
    "Personal Care", "Haircut", "Spa", "Beauty Products",
    "Gifts & Donations", "Charity", "Gifts",
    "Business Expenses", "Office Supplies", "Professional Services",
    
    # Savings & Investments
    "Savings Transfer", "Investment Transfer", "Retirement Contribution",
    
    # Uncategorized
    "Uncategorized",
]
```

**Rationale**:
- **User-friendly**: 50-60 categories easy to navigate (vs 900+ Plaid)
- **Budget-aligned**: Categories match common budget goals
- **Extensible**: Users can add custom categories via `add_custom_category()`

### Future: Plaid Sub-Categories (v2)

Add Plaid's granular sub-categories as opt-in feature:
```python
"Food & Dining" → ["Restaurants", "Coffee Shops", "Fast Food", "Groceries"]
"Transportation" → ["Gas Stations", "Parking", "Public Transit", "Ride Share"]
```

## Merchant Name Normalization

### Normalization Pipeline

```python
def normalize_merchant(name: str) -> str:
    """Normalize merchant name for categorization."""
    name = name.lower()
    name = re.sub(r'#\d+', '', name)                      # Remove store numbers
    name = re.sub(r'\d{2,}', '', name)                    # Remove long numbers
    name = re.sub(r'\b(inc|llc|corp|ltd|co)\b', '', name) # Remove legal entities
    name = re.sub(r'\s+', ' ', name).strip()              # Collapse whitespace
    return name
```

**Examples**:
- `"STARBUCKS #1234 SAN FRANCISCO CA"` → `"starbucks san francisco ca"`
- `"Shell Oil Company LLC"` → `"shell oil"`
- `"Target Store 5678"` → `"target store"`

### Fuzzy Matching (Optional, v2)

Use RapidFuzz for typo tolerance:
```python
from rapidfuzz import fuzz, process

def fuzzy_match_merchant(name: str, threshold: int = 85) -> tuple[str, int]:
    match, score, _ = process.extractOne(
        name, 
        KNOWN_MERCHANTS, 
        scorer=fuzz.partial_ratio
    )
    if score >= threshold:
        return match, score
    return None, 0
```

**Example**: `"SBUX 9012"` → fuzzy match → `"Starbucks"` (score: 75) → fallback to ML

## svc-infra Integration

### 1. Caching (svc-infra.cache)

**Strategy**: Cache predictions for 24 hours (reduces ML calls by 95%)

```python
from svc_infra.cache import resource, TTL_LONG

categorizer = resource("categorization", "merchant_name")

@categorizer.cache_read(suffix="category", ttl=TTL_LONG)  # 24h TTL
async def categorize_transaction(*, merchant_name: str) -> dict:
    category, confidence = engine.categorize(merchant_name)
    return {"category": category, "confidence": confidence}
```

**Cache Key**: `categorization:category:{merchant_name}`  
**Cache Tag**: `categorization:{merchant_name}`  
**TTL**: 24 hours (86400 seconds)

**Benefit**: 95% of predictions served from cache (sub-millisecond response)

### 2. User Overrides (svc-infra.db)

**Schema**:
```python
class CategoryOverride(ModelBase):
    __tablename__ = "category_overrides"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    merchant_name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'merchant_name'),
        Index('idx_user_merchant', 'user_id', 'merchant_name'),
    )
```

**Flow**:
1. User corrects prediction: "Starbucks" → "Coffee Shops" (from "Restaurants")
2. Store override in `category_overrides` table
3. Invalidate cache: `categorization:{merchant_name}`
4. Next prediction for same user checks overrides first

### 3. Batch Categorization (svc-infra.jobs)

**Strategy**: Nightly batch categorization of new transactions

```python
from svc_infra.jobs import easy_jobs

worker, scheduler = easy_jobs(app)

@scheduler.scheduled_job("cron", hour=2)  # 2 AM daily
async def batch_categorize_transactions():
    """Categorize all uncategorized transactions."""
    uncategorized = await get_uncategorized_transactions()
    
    for txn in uncategorized:
        category, confidence = engine.categorize(txn.merchant_name)
        await update_transaction_category(txn.id, category, confidence)
    
    # Retrain model with user corrections (active learning)
    await retrain_model_with_corrections()
```

### 4. Model Retraining (svc-infra.jobs + active learning)

**Strategy**: Weekly model retraining with user corrections

```python
@scheduler.scheduled_job("cron", day_of_week="sun", hour=3)  # Sunday 3 AM
async def retrain_categorization_model():
    """Retrain model with user corrections."""
    # Get user corrections from past week
    corrections = await get_category_overrides(days=7)
    
    if len(corrections) < 100:
        return  # Need at least 100 corrections to retrain
    
    # Append to training data
    training_data = load_base_training_data()
    training_data.extend(corrections)
    
    # Retrain model
    new_model = train_naive_bayes_model(training_data)
    
    # Validate accuracy (must be >= current model)
    accuracy = evaluate_model(new_model, validation_set)
    if accuracy >= current_model_accuracy:
        save_model(new_model, version=f"v{increment_version()}")
        deploy_model(new_model)
```

## Data Models

### TransactionCategory

```python
from pydantic import BaseModel, Field

class TransactionCategory(BaseModel):
    """Represents a transaction category."""
    name: str = Field(..., description="Category name (e.g., 'Coffee Shops')")
    parent: str | None = Field(None, description="Parent category (for hierarchical taxonomies)")
    keywords: list[str] = Field(default_factory=list, description="Keywords for rule matching")
    examples: list[str] = Field(default_factory=list, description="Example merchant names")
```

### CategoryRule

```python
class CategoryRule(BaseModel):
    """Represents a categorization rule."""
    pattern: str = Field(..., description="Merchant name pattern (exact or regex)")
    category: str = Field(..., description="Target category")
    is_regex: bool = Field(False, description="Whether pattern is regex")
    priority: int = Field(0, description="Rule priority (higher = checked first)")
```

### CategoryPrediction

```python
class CategoryPrediction(BaseModel):
    """Represents a category prediction result."""
    merchant_name: str = Field(..., description="Original merchant name")
    normalized_name: str = Field(..., description="Normalized merchant name")
    category: str = Field(..., description="Predicted category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    method: Literal["exact", "regex", "ml"] = Field(..., description="Prediction method")
    alternatives: list[tuple[str, float]] = Field(
        default_factory=list, 
        description="Alternative predictions [(category, confidence), ...]"
    )
```

## Implementation Plan

### Phase 1: Core Engine (v1 - MVP)

1. ✅ Create 50-60 category taxonomy (`categorization/taxonomy.py`)
2. ✅ Build merchant rule dict (50k+ entries, `categorization/rules.py`)
3. ✅ Implement regex pattern matching (1k+ patterns)
4. ✅ Implement hybrid categorization engine (`categorization/engine.py`)
5. ✅ Create `easy_categorization()` builder (`categorization/__init__.py`)
6. ✅ Integrate svc-infra.cache (24h TTL)
7. ✅ Create `add_categorization(app)` FastAPI helper
8. ✅ Write unit tests (90%+ accuracy on test set)
9. ✅ Document in docs/categorization.md

**Accuracy Target**: 90-95% (rule-based only)  
**Timeline**: 2 weeks

### Phase 2: ML Fallback (v2 - Enhancement)

1. ✅ Train Naive Bayes model on Plaid public dataset (100k+ transactions)
2. ✅ Implement ML fallback layer (confidence threshold 0.75)
3. ✅ Bundle pre-trained model in package (5MB)
4. ✅ Add fuzzy matching for typos (RapidFuzz)
5. ✅ Implement user override storage (svc-infra.db)
6. ✅ Add batch categorization job (svc-infra.jobs)
7. ✅ Write acceptance tests (real transactions)

**Accuracy Target**: 95-97% (hybrid rule + ML)  
**Timeline**: +2 weeks

### Phase 3: Active Learning (v3 - Optimization)

1. ✅ Implement user correction UI (prompt low-confidence predictions)
2. ✅ Store corrections in database (CategoryOverride model)
3. ✅ Implement weekly model retraining (svc-infra.jobs)
4. ✅ Add model versioning and A/B testing
5. ✅ Track accuracy metrics per model version
6. ✅ Auto-rollback if accuracy drops

**Accuracy Target**: 97-99% (improves over time with user corrections)  
**Timeline**: +2 weeks

## Consequences

### Positive

- ✅ **High Accuracy**: 95%+ for known merchants, 85%+ for unknown
- ✅ **Fast Cold Start**: Ships with 50k+ rules, no training period
- ✅ **Deterministic**: Same merchant → same category (user trust)
- ✅ **Resource Efficient**: No GPU, 5MB model, 1000 pred/sec
- ✅ **Self-Improving**: Active learning increases accuracy over time
- ✅ **svc-infra Integration**: Cache (24h TTL), jobs (batch), db (overrides)

### Negative

- ⚠️ **Dual Maintenance**: Must maintain both rules and ML model
- ⚠️ **Initial Training Data**: Need 100k+ labeled transactions for ML model (use Plaid dataset)
- ⚠️ **Storage Overhead**: 5MB model + 50k rules = ~8MB package size increase

### Risks & Mitigations

**Risk 1: Low ML Accuracy for Unknown Merchants**
- **Mitigation**: Set confidence threshold (0.75) and flag low-confidence predictions for user review

**Risk 2: Rule Maintenance Burden**
- **Mitigation**: Active learning reduces manual rule updates (model learns from user corrections)

**Risk 3: Model Drift (Accuracy Decreases Over Time)**
- **Mitigation**: Weekly retraining, accuracy monitoring, auto-rollback if accuracy drops

## Success Metrics

- **Accuracy**: 95%+ overall (96-98% target)
- **Response Time**: <100ms p95 (with caching)
- **User Correction Rate**: <5% (users correct <5% of predictions)
- **Cache Hit Rate**: >90% (24h TTL)
- **Model Size**: <10MB (including TF-IDF vectors)

## References

- Plaid Transaction Categories: https://plaid.com/docs/api/products/transactions/#transaction-category
- sklearn Naive Bayes: https://scikit-learn.org/stable/modules/naive_bayes.html
- Mint Categorization: https://mint.intuit.com/how-mint-works/security/
- Transaction Categorization Best Practices: https://plaid.com/blog/transaction-categorization/
- Research Document: docs/research/transaction-categorization.md (800+ lines)
