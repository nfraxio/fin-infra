# fin-infra-web API Coverage Analysis

**Date**: November 7, 2025  
**Purpose**: Deep analysis comparing fin-infra-web dashboard features with fin-infra package API endpoints

---

## Executive Summary

**Status**: 🟡 **PARTIAL COVERAGE** - Core financial data endpoints exist, but significant gaps in AI/LLM features, portfolio analytics, and document management.

**Key Findings**:
- ✅ **70% Coverage**: Basic financial data (accounts, transactions, holdings, net worth)
- 🟡 **30% Coverage**: Advanced features (AI insights, portfolio analytics, goals, documents, taxes)
- ❌ **0% Coverage**: Budget tracking, cash flow analysis, crypto portfolio, growth projections

---

## Dashboard Pages Analysis

### 1. Overview Dashboard (`/dashboard`)

**UI Components**:
- Overview KPIs (Net Worth, Total Cash, Total Investments, Total Debt, Savings Rate, etc.)
- Portfolio Allocation Chart
- Performance Timeline
- Cash Flow Chart
- Portfolio Holdings Summary
- Recent Activity Feed
- AI Insights Panel
- Accountability Checklist

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Net Worth KPI** | `GET /net-worth/current` | ✅ **COVERED** | Returns total_net_worth, total_assets, total_liabilities |
| **Total Cash** | `GET /banking/accounts` | ✅ **COVERED** | Sum checking+savings account balances |
| **Total Investments** | `GET /brokerage/account` | ✅ **COVERED** | Returns portfolio_value from brokerage provider |
| **Total Debt** | `GET /banking/accounts` | ✅ **COVERED** | Sum credit card balances (negative) |
| **Savings Rate** | ❌ **MISSING** | ❌ **MISSING** | No endpoint calculates savings rate |
| **Portfolio Allocation** | `GET /brokerage/positions` | 🟡 **PARTIAL** | Returns positions, but UI needs aggregation by asset class |
| **Performance Timeline** | `GET /brokerage/portfolio/history` | ✅ **COVERED** | Returns historical portfolio values |
| **Cash Flow** | ❌ **MISSING** | ❌ **MISSING** | No income vs expenses analysis endpoint |
| **Holdings Summary** | `GET /brokerage/positions` | ✅ **COVERED** | Returns all open positions |
| **Recent Activity** | `GET /banking/transactions` | ✅ **COVERED** | Returns recent transactions |
| **AI Insights** | `GET /net-worth/insights` | 🟡 **PARTIAL** | V2 LLM insights exist (4 types), but UI expects different format |

**Coverage Score**: **60%** (6/10 features fully covered)

**Missing Endpoints**:
1. **Savings Rate Calculation**: Need `GET /analytics/savings-rate?user_id=...&period=30d`
2. **Cash Flow Analysis**: Need `GET /analytics/cash-flow?user_id=...&start_date=...&end_date=...`
3. **Asset Class Aggregation**: Need endpoint to group positions by asset class (stocks, bonds, crypto, real estate)

---

### 2. Accounts Page (`/dashboard/accounts`)

**UI Components**:
- Account cards (Checking, Savings, Credit Card, Investment)
- Account balance history sparklines
- Total cash, total debt, total investments summaries
- Last sync timestamps
- Account status indicators (active, needs_update, disconnected)
- Next bill due dates

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **List Accounts** | `GET /banking/accounts` | ✅ **COVERED** | Returns all account details |
| **Account Balances** | `GET /banking/accounts` | ✅ **COVERED** | Current balance per account |
| **Balance History** | ❌ **MISSING** | ❌ **MISSING** | No historical balance tracking |
| **Account Status** | ❌ **MISSING** | ❌ **MISSING** | No status tracking (active, needs_update, disconnected) |
| **Next Bill Due** | ❌ **MISSING** | ❌ **MISSING** | No recurring bill tracking integrated |
| **Sync Timestamp** | ❌ **MISSING** | ❌ **MISSING** | No last_synced field in response |

**Coverage Score**: **33%** (2/6 features fully covered)

**Missing Endpoints**:
1. **Account Balance History**: Need `GET /banking/accounts/{account_id}/history?days=90`
2. **Account Status Tracking**: Need status field in account response + webhook for disconnections
3. **Recurring Bills**: Need integration with `/recurring/detect` endpoint for bill reminders
4. **Sync Status**: Need last_synced timestamp in all financial data responses

---

### 3. Transactions Page (`/dashboard/transactions`)

**UI Components**:
- Transaction list with filters (category, date range, amount range, merchant)
- Transaction insights (top merchants, category breakdown, recurring detection)
- Transaction search
- Transaction categorization
- Recurring transaction badges
- Flagged transaction indicators
- Transfer detection

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **List Transactions** | `GET /banking/transactions` | ✅ **COVERED** | Returns transaction history |
| **Transaction Search** | ❌ **MISSING** | ❌ **MISSING** | No search/filter params |
| **Categorization** | `POST /categorization/predict` | ✅ **COVERED** | ML-based category prediction |
| **Recurring Detection** | `POST /recurring/detect` | ✅ **COVERED** | Detects recurring patterns |
| **Category Stats** | `GET /categorization/stats` | ✅ **COVERED** | Category usage statistics |
| **Transaction Insights** | ❌ **MISSING** | ❌ **MISSING** | No top merchants or spending insights |
| **Flagged Transactions** | ❌ **MISSING** | ❌ **MISSING** | No fraud/anomaly detection |
| **Transfer Detection** | ❌ **MISSING** | ❌ **MISSING** | No transfer identification logic |

**Coverage Score**: **50%** (4/8 features fully covered)

**Missing Endpoints**:
1. **Transaction Search/Filtering**: Add query params to `GET /banking/transactions?merchant=...&category=...&min_amount=...&max_amount=...`
2. **Spending Insights**: Need `GET /analytics/spending-insights?user_id=...&period=30d` (top merchants, category trends)
3. **Fraud Detection**: Need `POST /security/detect-anomalies` endpoint
4. **Transfer Detection**: Add transfer_type field to categorization response (internal_transfer, external_transfer)

---

### 4. Portfolio Page (`/dashboard/portfolio`)

**UI Components**:
- Portfolio KPIs (Total Value, Total Gain, Day Change, YTD Return)
- Holdings table (symbol, shares, avg price, current price, gain/loss)
- Allocation grid (by asset class: stocks, bonds, cash, crypto, real estate)
- Performance comparison vs SPY benchmark
- AI portfolio insights
- Rebalancing preview
- Scenario playbook (what-if analysis)

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Portfolio Value** | `GET /brokerage/account` | ✅ **COVERED** | Returns portfolio_value |
| **Holdings List** | `GET /brokerage/positions` | ✅ **COVERED** | Returns all positions with P&L |
| **Day Change** | `GET /brokerage/portfolio/history` | 🟡 **PARTIAL** | Can calculate from history, but not explicit |
| **YTD Return** | ❌ **MISSING** | ❌ **MISSING** | No YTD calculation endpoint |
| **Allocation by Asset Class** | ❌ **MISSING** | ❌ **MISSING** | No asset class grouping |
| **Performance vs SPY** | ❌ **MISSING** | ❌ **MISSING** | No benchmark comparison |
| **AI Insights** | `GET /net-worth/insights?type=asset_allocation` | 🟡 **PARTIAL** | V2 LLM insights exist, but different format |
| **Rebalancing Suggestions** | ❌ **MISSING** | ❌ **MISSING** | No rebalancing logic |
| **Scenario Analysis** | ❌ **MISSING** | ❌ **MISSING** | No what-if modeling |

**Coverage Score**: **22%** (2/9 features fully covered)

**Missing Endpoints**:
1. **Portfolio Analytics**: Need `GET /analytics/portfolio?user_id=...` with YTD/MTD/1Y returns
2. **Asset Allocation**: Need `GET /analytics/allocation?user_id=...` grouped by asset class
3. **Benchmark Comparison**: Need `GET /analytics/performance?user_id=...&benchmark=SPY`
4. **Rebalancing Engine**: Need `POST /analytics/rebalancing` with target allocation input
5. **Scenario Modeling**: Need `POST /analytics/scenario` for what-if projections

---

### 5. Goals Page (`/dashboard/goals`)

**UI Components**:
- Goal cards (Retirement, Home Purchase, Debt-Free, Emergency Fund)
- Goal progress bars with milestones
- Monthly target vs actual savings
- ETA to goal completion
- Goal acceleration recommendations
- Funding source allocation
- Goal celebration messages

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Goal Validation** | `POST /net-worth/goals` | ✅ **COVERED** | Validates goal feasibility with LLM |
| **Goal Progress** | `GET /net-worth/goals/{goal_id}/progress` | 🟡 **STUB** | Returns 501 (not implemented) |
| **Goal Recommendations** | `GET /net-worth/insights?type=goal_recommendations` | ✅ **COVERED** | LLM suggests personalized goals |
| **Monthly Savings Tracking** | ❌ **MISSING** | ❌ **MISSING** | No savings rate tracking |
| **Goal Milestones** | ❌ **MISSING** | ❌ **MISSING** | No milestone tracking |
| **Funding Allocation** | ❌ **MISSING** | ❌ **MISSING** | No account-to-goal mapping |
| **Goal CRUD** | ❌ **MISSING** | ❌ **MISSING** | No create/update/delete endpoints |

**Coverage Score**: **29%** (2/7 features fully covered)

**Missing Endpoints**:
1. **Goal CRUD**: Need full REST API:
   - `POST /goals` - Create goal
   - `GET /goals?user_id=...` - List goals
   - `PATCH /goals/{goal_id}` - Update goal
   - `DELETE /goals/{goal_id}` - Delete goal
2. **Goal Progress Implementation**: Complete stub `GET /net-worth/goals/{goal_id}/progress`
3. **Savings Tracking**: Need `GET /analytics/savings-rate?user_id=...&goal_id=...`
4. **Milestone Management**: Need milestone CRUD in goals API
5. **Funding Allocation**: Need account-to-goal mapping in goals data model

---

### 6. Budget Page (`/dashboard/budget`)

**UI Components**:
- Budget category cards (Housing, Transportation, Food, Entertainment, etc.)
- Spent vs budgeted progress bars
- Over-budget alerts
- Budget adjustment recommendations
- Spending trends by category
- Rollover budget logic

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Budget CRUD** | ❌ **MISSING** | ❌ **MISSING** | No budget management endpoints |
| **Category Spending** | `GET /categorization/stats` | 🟡 **PARTIAL** | Has category counts, but not spending totals |
| **Budget Tracking** | ❌ **MISSING** | ❌ **MISSING** | No spent vs budgeted comparison |
| **Overspending Alerts** | ❌ **MISSING** | ❌ **MISSING** | No alert system |
| **Budget Insights** | ❌ **MISSING** | ❌ **MISSING** | No AI recommendations |

**Coverage Score**: **0%** (0/5 features covered)

**Missing Endpoints**:
1. **Budget Management**: Full REST API needed:
   - `POST /budgets` - Create budget
   - `GET /budgets?user_id=...` - List budgets
   - `PATCH /budgets/{budget_id}` - Update budget
   - `DELETE /budgets/{budget_id}` - Delete budget
2. **Budget Tracking**: Need `GET /budgets/{budget_id}/progress?period=current_month`
3. **Spending Analysis**: Enhance `/categorization/stats` to include total amounts per category
4. **Budget Alerts**: Need webhook system for overspending notifications

---

### 7. Cash Flow Page (`/dashboard/cash-flow`)

**UI Components**:
- Income vs expenses chart (monthly trend)
- Net cash flow calculation
- Income sources breakdown
- Expense categories breakdown
- Recurring income/expenses identification
- Cash flow projections (3/6/12 months)

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Income Calculation** | ❌ **MISSING** | ❌ **MISSING** | No income aggregation |
| **Expense Calculation** | ❌ **MISSING** | ❌ **MISSING** | No expense aggregation |
| **Cash Flow Trend** | ❌ **MISSING** | ❌ **MISSING** | No time-series analysis |
| **Income Sources** | `POST /recurring/detect` | 🟡 **PARTIAL** | Can detect recurring income, but not aggregated |
| **Recurring Expenses** | `POST /recurring/detect` | 🟡 **PARTIAL** | Detects patterns, but no summary |
| **Cash Flow Projections** | ❌ **MISSING** | ❌ **MISSING** | No forecasting logic |

**Coverage Score**: **0%** (0/6 features covered)

**Missing Endpoints**:
1. **Cash Flow Analysis**: Need `GET /analytics/cash-flow?user_id=...&start_date=...&end_date=...`
   - Returns: `{income_total, expense_total, net_cash_flow, income_by_source[], expenses_by_category[]}`
2. **Cash Flow Projections**: Need `POST /analytics/cash-flow/forecast` with historical data
3. **Recurring Summary**: Need `GET /recurring/summary?user_id=...` aggregating recurring income/expenses

---

### 8. Crypto Page (`/dashboard/crypto`)

**UI Components**:
- Crypto portfolio value
- Crypto holdings list (symbol, quantity, avg price, current price, gain/loss)
- Crypto allocation chart
- Crypto market trends
- Crypto tax implications (capital gains)
- Crypto insights (AI-powered)

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Crypto Holdings** | `GET /crypto/portfolio` | ✅ **COVERED** | Returns crypto balances |
| **Crypto Prices** | `GET /crypto/prices` | ✅ **COVERED** | Real-time crypto prices |
| **Crypto Tax** | `POST /tax/crypto-gains` | ✅ **COVERED** | Capital gains calculation |
| **Portfolio Value** | `GET /crypto/portfolio` | ✅ **COVERED** | Total portfolio value |
| **Crypto Insights** | ❌ **MISSING** | ❌ **MISSING** | No AI crypto insights |
| **Market Trends** | ❌ **MISSING** | ❌ **MISSING** | No crypto market analysis |

**Coverage Score**: **67%** (4/6 features covered)

**Missing Endpoints**:
1. **Crypto Insights**: Add `GET /crypto/insights?user_id=...` (LLM-powered recommendations)
2. **Market Trends**: Add `GET /crypto/market-trends?symbols=BTC,ETH` (aggregate market data)

---

### 9. Documents Page (`/dashboard/documents`)

**UI Components**:
- Document list (tax forms, statements, reports)
- Document filters (type, institution, year, account)
- Document insights (AI-powered analysis)
- Document upload
- Document search

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **List Tax Documents** | `GET /tax/documents` | ✅ **COVERED** | Returns W-2, 1099 forms |
| **Get Specific Document** | `GET /tax/documents/{document_id}` | ✅ **COVERED** | Returns document details |
| **Document Upload** | ❌ **MISSING** | ❌ **MISSING** | No file upload endpoint |
| **Document Search** | ❌ **MISSING** | ❌ **MISSING** | No search functionality |
| **Document Insights** | ❌ **MISSING** | ❌ **MISSING** | No AI analysis |
| **Statement Documents** | ❌ **MISSING** | ❌ **MISSING** | No brokerage/banking statements |

**Coverage Score**: **33%** (2/6 features covered)

**Missing Endpoints**:
1. **Document Upload**: Need `POST /documents/upload` with file handling
2. **Document Management**: Full CRUD needed:
   - `GET /documents?user_id=...&type=...&year=...`
   - `DELETE /documents/{document_id}`
3. **Document Insights**: Need `POST /documents/{document_id}/analyze` (LLM-powered)
4. **Brokerage/Banking Statements**: Extend tax documents to include all statement types

---

### 10. Taxes Page (`/dashboard/taxes`)

**UI Components**:
- Tax liability estimate
- Tax documents list
- Tax-loss harvesting opportunities
- Crypto capital gains report
- Tax bracket visualization
- State tax comparison

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Tax Liability** | `POST /tax/tax-liability` | ✅ **COVERED** | Estimates federal/state tax |
| **Tax Documents** | `GET /tax/documents` | ✅ **COVERED** | Returns W-2, 1099 forms |
| **Crypto Gains** | `POST /tax/crypto-gains` | ✅ **COVERED** | Capital gains calculation |
| **Tax-Loss Harvesting** | ❌ **MISSING** | ❌ **MISSING** | No TLH logic |
| **Tax Bracket Viz** | ❌ **MISSING** | ❌ **MISSING** | No bracket analysis |
| **State Comparison** | ❌ **MISSING** | ❌ **MISSING** | No multi-state analysis |

**Coverage Score**: **50%** (3/6 features covered)

**Missing Endpoints**:
1. **Tax-Loss Harvesting**: Need `GET /tax/tlh-opportunities?user_id=...` analyzing positions for TLH
2. **Tax Bracket Analysis**: Enhance `/tax/tax-liability` to return bracket breakdown
3. **State Tax Comparison**: Need `POST /tax/compare-states` endpoint

---

### 11. Growth Page (`/dashboard/growth`)

**UI Components**:
- Net worth growth projections
- Compound interest calculator
- Retirement savings projections
- Goal timeline forecasts
- What-if scenarios (income changes, savings rate changes)

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Net Worth Projections** | ❌ **MISSING** | ❌ **MISSING** | No forecasting endpoint |
| **Compound Interest** | ❌ **MISSING** | ❌ **MISSING** | No calculator endpoint |
| **Retirement Projections** | 🟡 **PARTIAL** | 🟡 **PARTIAL** | Goal validation includes some projection logic |
| **Goal Timelines** | `POST /net-worth/goals` | 🟡 **PARTIAL** | Returns projected_completion_date |
| **Scenario Modeling** | ❌ **MISSING** | ❌ **MISSING** | No what-if API |

**Coverage Score**: **20%** (1/5 features covered)

**Missing Endpoints**:
1. **Growth Projections**: Need `POST /analytics/forecast-net-worth` with assumptions
2. **Compound Interest Calculator**: Need `POST /analytics/compound-interest` helper
3. **Scenario Modeling**: Need `POST /analytics/scenario` for what-if analysis

---

### 12. Insights Page (`/dashboard/insights`)

**UI Components**:
- AI-generated insights feed
- Pinned insights
- Insight categories (spending, investment, goals, alerts)
- Insight data points
- Insight explanations
- Insight actions (view details, dismiss, pin)

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Wealth Trends** | `GET /net-worth/insights?type=wealth_trends` | ✅ **COVERED** | LLM analysis of net worth |
| **Debt Reduction** | `GET /net-worth/insights?type=debt_reduction` | ✅ **COVERED** | LLM debt payoff plan |
| **Goal Recommendations** | `GET /net-worth/insights?type=goal_recommendations` | ✅ **COVERED** | LLM suggested goals |
| **Asset Allocation** | `GET /net-worth/insights?type=asset_allocation` | ✅ **COVERED** | LLM portfolio advice |
| **Spending Insights** | ❌ **MISSING** | ❌ **MISSING** | No spending analysis |
| **Investment Insights** | ❌ **MISSING** | ❌ **MISSING** | No investment recommendations |
| **Alert Insights** | ❌ **MISSING** | ❌ **MISSING** | No anomaly detection insights |
| **Insights Feed** | ❌ **MISSING** | ❌ **MISSING** | No unified insights API |

**Coverage Score**: **50%** (4/8 features covered)

**Missing Endpoints**:
1. **Insights Feed**: Need `GET /insights?user_id=...&category=...` aggregating all insight types
2. **Spending Insights**: Need endpoint analyzing spending patterns
3. **Investment Insights**: Need portfolio optimization recommendations
4. **Alert Insights**: Need fraud/anomaly detection insights

---

### 13. Billing Page (`/dashboard/billing`)

**UI Components**:
- Subscription plan details
- Usage metrics
- Payment method
- Billing history
- Invoice download

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Billing Management** | ❌ **MISSING** | ❌ **NOT IN FIN-INFRA** | Handled by svc-infra billing module |

**Coverage Score**: **N/A** - Billing is svc-infra responsibility, not fin-infra

---

### 14. Profile/Settings Pages

**UI Components**:
- User profile settings
- Privacy settings (data masking)
- Notification preferences
- Connected accounts management
- Security settings (MFA, password)

**fin-infra API Coverage**:

| Component | Endpoint | Status | Notes |
|-----------|----------|--------|-------|
| **Profile Management** | ❌ **MISSING** | ❌ **NOT IN FIN-INFRA** | Handled by svc-infra auth module |
| **Privacy Settings** | `POST /security/encrypt` | 🟡 **PARTIAL** | Encryption helpers exist |
| **Account Connections** | `POST /banking/link` | ✅ **COVERED** | Plaid/Teller account linking |

**Coverage Score**: **N/A** - Most settings are svc-infra responsibility

---

## Summary: Missing Endpoints by Priority

### 🔴 **HIGH PRIORITY** (Critical for MVP)

1. **Budget Management**: Full CRUD API for budgets + tracking
   ```
   POST   /budgets
   GET    /budgets?user_id=...
   PATCH  /budgets/{budget_id}
   DELETE /budgets/{budget_id}
   GET    /budgets/{budget_id}/progress
   ```

2. **Cash Flow Analysis**: Income vs expenses aggregation
   ```
   GET /analytics/cash-flow?user_id=...&period=...
   ```

3. **Savings Rate Calculation**: Track savings over time
   ```
   GET /analytics/savings-rate?user_id=...&period=...
   ```

4. **Goal Management**: Full CRUD for financial goals
   ```
   POST   /goals
   GET    /goals?user_id=...
   PATCH  /goals/{goal_id}
   DELETE /goals/{goal_id}
   GET    /goals/{goal_id}/progress (complete stub)
   ```

5. **Transaction Search/Filtering**: Enhanced query params
   ```
   GET /banking/transactions?merchant=...&category=...&min_amount=...&max_amount=...
   ```

6. **Account Balance History**: Historical balance tracking
   ```
   GET /banking/accounts/{account_id}/history?days=90
   ```

### 🟡 **MEDIUM PRIORITY** (Important for complete experience)

7. **Portfolio Analytics**: YTD/MTD returns, asset allocation
   ```
   GET /analytics/portfolio?user_id=...
   GET /analytics/allocation?user_id=...
   GET /analytics/performance?user_id=...&benchmark=SPY
   ```

8. **Spending Insights**: Top merchants, category trends
   ```
   GET /analytics/spending-insights?user_id=...&period=30d
   ```

9. **Recurring Summary**: Aggregated recurring income/expenses
   ```
   GET /recurring/summary?user_id=...
   ```

10. **Document Management**: Upload, search, insights
    ```
    POST /documents/upload
    GET  /documents?user_id=...&type=...
    POST /documents/{document_id}/analyze
    ```

11. **Tax-Loss Harvesting**: TLH opportunity detection
    ```
    GET /tax/tlh-opportunities?user_id=...
    ```

### 🟢 **LOW PRIORITY** (Nice-to-have enhancements)

12. **Growth Projections**: Net worth forecasting
    ```
    POST /analytics/forecast-net-worth
    POST /analytics/compound-interest
    ```

13. **Scenario Modeling**: What-if analysis
    ```
    POST /analytics/scenario
    ```

14. **Rebalancing Engine**: Portfolio rebalancing suggestions
    ```
    POST /analytics/rebalancing
    ```

15. **Insights Feed**: Unified AI insights API
    ```
    GET /insights?user_id=...&category=...
    ```

16. **Crypto Insights**: AI-powered crypto recommendations
    ```
    GET /crypto/insights?user_id=...
    ```

---

## API Design Recommendations

### 1. **Analytics Module** (New Domain)

Create a new analytics domain in fin-infra to consolidate all calculation/analysis endpoints:

```python
# src/fin_infra/analytics/__init__.py
from .ease import easy_analytics
from .add import add_analytics

# src/fin_infra/analytics/add.py
def add_analytics(app: FastAPI, prefix="/analytics") -> AnalyticsEngine:
    """Mount analytics endpoints:
    - GET /analytics/cash-flow
    - GET /analytics/savings-rate
    - GET /analytics/spending-insights
    - GET /analytics/portfolio
    - GET /analytics/allocation
    - GET /analytics/performance
    - POST /analytics/forecast-net-worth
    - POST /analytics/scenario
    - POST /analytics/rebalancing
    """
```

### 2. **Budgets Module** (New Domain)

Create dedicated budget management:

```python
# src/fin_infra/budgets/__init__.py
from .ease import easy_budgets
from .add import add_budgets

# src/fin_infra/budgets/add.py
def add_budgets(app: FastAPI, prefix="/budgets") -> BudgetTracker:
    """Mount budget endpoints:
    - POST /budgets
    - GET /budgets
    - PATCH /budgets/{budget_id}
    - DELETE /budgets/{budget_id}
    - GET /budgets/{budget_id}/progress
    """
```

### 3. **Goals Module** (Expand Existing)

Enhance net_worth/goals.py with full CRUD:

```python
# src/fin_infra/net_worth/add.py
@router.post("/goals")
async def create_goal(...): ...

@router.get("/goals")
async def list_goals(...): ...

@router.patch("/goals/{goal_id}")
async def update_goal(...): ...

@router.delete("/goals/{goal_id}")
async def delete_goal(...): ...

@router.get("/goals/{goal_id}/progress")
async def get_goal_progress(...):
    # Complete the 501 stub implementation
```

### 4. **Documents Module** (New Domain)

Create document management with OCR:

```python
# src/fin_infra/documents/__init__.py
from .ease import easy_documents
from .add import add_documents

# src/fin_infra/documents/add.py
def add_documents(app: FastAPI, prefix="/documents") -> DocumentManager:
    """Mount document endpoints:
    - POST /documents/upload
    - GET /documents
    - GET /documents/{document_id}
    - DELETE /documents/{document_id}
    - POST /documents/{document_id}/analyze (AI)
    """
```

---

## Next Steps

### Immediate Actions

1. **Prioritize High Priority Endpoints**: Implement Budget, Cash Flow, Savings Rate, Goal CRUD first
2. **Create Analytics Module**: Consolidate all calculation endpoints in one place
3. **Expand Net Worth Module**: Complete goal management implementation
4. **Document Gaps in Plans.md**: Add new sections for missing features

### Long-term Strategy

1. **API-First Development**: Build all new dashboard features with API-first approach
2. **Mock Data Removal**: Replace all mock data in fin-infra-web with real API calls
3. **Comprehensive Testing**: Add acceptance tests for all new endpoints
4. **Documentation**: Update docs/api.md with all new endpoints

---

## Conclusion

**Overall Coverage**: **~50%** of fin-infra-web dashboard features are covered by fin-infra APIs

**Critical Gaps**:
- Budget management (0% coverage)
- Cash flow analysis (0% coverage)
- Portfolio analytics (22% coverage)
- Goal management (29% coverage, stub implementation)
- Document management (33% coverage)

**Strong Coverage**:
- Banking data (70% coverage)
- Brokerage data (70% coverage)
- Crypto data (67% coverage)
- Tax data (50% coverage)
- Categorization (50% coverage)

**Recommendation**: Focus on implementing HIGH PRIORITY endpoints first (Budget, Cash Flow, Goals, Analytics) before moving to MEDIUM and LOW priority features. This will provide a complete MVP experience for users.
