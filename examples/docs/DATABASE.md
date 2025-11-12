# Database Guide

Complete guide to database setup, models, migrations, and schema for fin-infra template.

## Table of Contents

- [Overview](#overview)
- [Quick Setup](#quick-setup)
- [Database Models](#database-models)
- [Migrations](#migrations)
- [Schema Reference](#schema-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The fin-infra template uses **SQLAlchemy 2.0** with support for multiple databases:

- **Development**: SQLite (default, zero configuration)
- **Production**: PostgreSQL (recommended), MySQL, SQL Server

All database migrations are managed by **Alembic** (via svc-infra CLI).

---

## Quick Setup

### Option 1: SQLite (Development)

**Zero configuration** - works out of the box:

```bash
# Create tables (no migrations)
poetry run python create_tables.py

# Or with migrations
poetry run python -m svc_infra.db init --project-root .
poetry run python -m svc_infra.db setup-and-migrate --project-root .
```

SQLite database created at: `./dev.db`

### Option 2: PostgreSQL (Production)

**1. Start PostgreSQL (via Docker)**:

```bash
docker run -d \
  --name fin-infra-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=fininfra \
  -e POSTGRES_DB=fininfra \
  -p 5432:5432 \
  postgres:15
```

**2. Configure `.env`**:

```bash
SQL_URL=postgresql+asyncpg://fininfra:password@localhost:5432/fininfra
```

**3. Run migrations**:

```bash
cd examples
poetry run python -m svc_infra.db setup-and-migrate --project-root .
```

### Option 3: Existing Database

Connect to an existing database:

```bash
# .env
SQL_URL=postgresql+asyncpg://user:pass@host:port/dbname

# Run migrations to create fin-infra tables
cd examples
poetry run python -m svc_infra.db upgrade head --project-root .
```

---

## Database Models

### Financial Data Models

Located in `src/main.py` (or your app module):

#### 1. User (Authentication)

```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Purpose**: User authentication and profile.

#### 2. BankConnection

```python
class BankConnection(Base):
    __tablename__ = "bank_connections"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    access_token: Mapped[str] = mapped_column(String(500))  # Encrypted
    item_id: Mapped[str] = mapped_column(String(100))
    institution_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Purpose**: Store Plaid/Teller connections per user.

#### 3. Account

```python
class Account(Base):
    __tablename__ = "accounts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    connection_id: Mapped[str] = mapped_column(ForeignKey("bank_connections.id"))
    account_id: Mapped[str] = mapped_column(String(100))  # Provider ID
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))  # checking, savings, credit, etc.
    subtype: Mapped[str] = mapped_column(String(50))
    balance: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Purpose**: User's linked bank accounts.

#### 4. Transaction

```python
class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    transaction_id: Mapped[str] = mapped_column(String(100))  # Provider ID
    amount: Mapped[float] = mapped_column(Float)
    date: Mapped[date] = mapped_column(Date)
    name: Mapped[str] = mapped_column(String(255))
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pending: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Purpose**: Transaction history for budgeting and analytics.

#### 5. Budget

```python
class Budget(Base):
    __tablename__ = "budgets"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))  # monthly, weekly, annual
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    categories: Mapped[dict] = mapped_column(JSON)  # {"Food": 500, "Transport": 200}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Purpose**: User budget definitions.

#### 6. Goal

```python
class Goal(Base):
    __tablename__ = "goals"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    target_amount: Mapped[float] = mapped_column(Float)
    current_amount: Mapped[float] = mapped_column(Float, default=0.0)
    target_date: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String(50))  # low, medium, high
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Purpose**: Financial goals (emergency fund, vacation, etc.).

#### 7. NetWorthSnapshot

```python
class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    snapshot_date: Mapped[date] = mapped_column(Date)
    total_assets: Mapped[float] = mapped_column(Float)
    total_liabilities: Mapped[float] = mapped_column(Float)
    net_worth: Mapped[float] = mapped_column(Float)
    assets_breakdown: Mapped[dict] = mapped_column(JSON)
    liabilities_breakdown: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Purpose**: Historical net worth tracking.

#### 8. Document

```python
class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(50))  # w2, 1099, receipt, etc.
    file_path: Mapped[str] = mapped_column(String(500))
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Purpose**: Store financial documents with OCR data.

---

## Migrations

### Initialize Migrations

First-time setup:

```bash
cd examples
poetry run python -m svc_infra.db init --project-root .
```

Creates:
- `alembic.ini` - Alembic configuration
- `migrations/` - Migration scripts directory
- `migrations/env.py` - Migration environment

### Create Migration

After modifying models:

```bash
poetry run python -m svc_infra.db revision \
  --autogenerate \
  -m "Add user preferences table" \
  --project-root .
```

This generates a new migration file in `migrations/versions/`.

### Apply Migrations

**Upgrade to latest**:

```bash
poetry run python -m svc_infra.db upgrade head --project-root .
```

**Downgrade one version**:

```bash
poetry run python -m svc_infra.db downgrade -1 --project-root .
```

**Check current version**:

```bash
poetry run python -m svc_infra.db current --project-root .
```

**View migration history**:

```bash
poetry run python -m svc_infra.db history --project-root .
```

### One-Command Setup

For new databases:

```bash
poetry run python -m svc_infra.db setup-and-migrate --project-root .
```

This:
1. Initializes migrations (if not already)
2. Creates migration for all models
3. Applies migrations to database

---

## Schema Reference

### Entity Relationships

```
User
 ├── BankConnection (1:N)
 │    └── Account (1:N)
 │         └── Transaction (1:N)
 ├── Budget (1:N)
 ├── Goal (1:N)
 ├── NetWorthSnapshot (1:N)
 └── Document (1:N)
```

### Indexes

Recommended indexes for performance:

```python
# In models
class Transaction(Base):
    __tablename__ = "transactions"
    
    # ... columns ...
    
    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "date"),
        Index("ix_transactions_account", "account_id"),
    )
```

### Constraints

Foreign key constraints ensure data integrity:

- `user_id` references `users.id` (CASCADE on delete)
- `account_id` references `accounts.id` (CASCADE on delete)
- `connection_id` references `bank_connections.id` (CASCADE on delete)

---

## Best Practices

### 1. Use Async Sessions

```python
from svc_infra.db.sql import get_async_session

async with get_async_session() as session:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
```

### 2. Encrypt Sensitive Data

```python
from svc_infra.security import encrypt_field

class BankConnection(Base):
    # ...
    _access_token: Mapped[str] = mapped_column("access_token", String(500))
    
    @property
    def access_token(self) -> str:
        return decrypt_field(self._access_token)
    
    @access_token.setter
    def access_token(self, value: str):
        self._access_token = encrypt_field(value)
```

### 3. Use Soft Deletes

For audit trails:

```python
class Account(Base):
    # ...
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Query only active accounts
    # session.query(Account).filter(Account.deleted_at.is_(None))
```

### 4. Batch Inserts

For performance:

```python
async with get_async_session() as session:
    transactions = [
        Transaction(user_id=user_id, amount=amt, ...)
        for amt in amounts
    ]
    session.add_all(transactions)
    await session.commit()
```

### 5. Use Transactions

For data consistency:

```python
async with get_async_session() as session:
    async with session.begin():
        # All or nothing
        session.add(account)
        session.add(transaction)
        # Commits automatically if no exception
```

---

## Troubleshooting

### Error: "database is locked" (SQLite)

**Cause**: Concurrent writes to SQLite.

**Solution**:
- Use PostgreSQL for production
- Or add timeout: `SQL_URL=sqlite+aiosqlite:///dev.db?timeout=20`

### Error: "relation does not exist"

**Cause**: Migrations not applied.

**Solution**:
```bash
cd examples
poetry run python -m svc_infra.db upgrade head --project-root .
```

### Error: "asyncpg not installed"

**Cause**: Missing PostgreSQL driver.

**Solution**:
```bash
poetry add asyncpg
# Or install fin-infra with pg extra
poetry add fin-infra[pg]
```

### Error: "column does not exist after adding new field"

**Cause**: Model changed but migration not created.

**Solution**:
```bash
poetry run python -m svc_infra.db revision --autogenerate -m "Add new field" --project-root .
poetry run python -m svc_infra.db upgrade head --project-root .
```

### Resetting Database

**Development** (SQLite):
```bash
rm dev.db
poetry run python create_tables.py
# Or
poetry run python -m svc_infra.db setup-and-migrate --project-root .
```

**Production** (PostgreSQL):
```bash
# Downgrade all migrations
poetry run python -m svc_infra.db downgrade base --project-root .

# Or drop database and recreate
docker exec -it fin-infra-db psql -U fininfra -c "DROP DATABASE fininfra; CREATE DATABASE fininfra;"

# Re-apply migrations
poetry run python -m svc_infra.db upgrade head --project-root .
```

---

## Advanced Topics

### Custom Types

```python
from sqlalchemy import TypeDecorator, String
import json

class JSONEncodedDict(TypeDecorator):
    impl = String
    
    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value else None
    
    def process_result_value(self, value, dialect):
        return json.loads(value) if value else None
```

### Database Seeding

```python
# scripts/seed_data.py
async def seed_test_data():
    async with get_async_session() as session:
        user = User(id="test_user", email="test@example.com")
        session.add(user)
        
        budget = Budget(
            user_id="test_user",
            name="Test Budget",
            type="monthly",
            start_date=date.today(),
            categories={"Food": 500}
        )
        session.add(budget)
        
        await session.commit()
```

### Query Performance

Use `select()` with relationships:

```python
from sqlalchemy.orm import selectinload

stmt = select(User).options(
    selectinload(User.accounts).selectinload(Account.transactions)
)
result = await session.execute(stmt)
users = result.scalars().all()
```

---

## Next Steps

- **Configure providers**: See [PROVIDERS.md](PROVIDERS.md)
- **Try examples**: Check [USAGE.md](../USAGE.md)
- **Explore capabilities**: Read [CAPABILITIES.md](CAPABILITIES.md)

---

**Questions?** Open an issue or check the main [README.md](../README.md).
