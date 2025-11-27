# Persistence Strategy for fin-infra

## Executive Summary

**Decision**: fin-infra will NOT own database tables. Applications own their persistence layer.

**Why**: fin-infra is a **library** (like stripe-python, plaid-python), not a **framework** (like Django). Libraries should be stateless and let applications control their data schema.

**Solution**: Provide scaffold CLI following svc-infra's pattern:
```bash
# Generate models + schemas + repository for your app
fin-infra scaffold budgets --dest-dir app/models/ --include-tenant --include-soft-delete

# Uses svc-infra's ModelBase for Alembic migrations
# Generated files are starting points - customize for your needs
```

**Implementation**: Template-based code generation with:
- `.tmpl` files in `fin_infra/{domain}/templates/`
- Typer CLI with customization flags
- `string.Template.safe_substitute()` for variable substitution
- Overwrite protection and clear result reporting

**Timeline**: 10 phases over ~30-40 hours of development

---

## Context

fin-infra currently has multiple TODO comments indicating planned database persistence:
- Budgets: 6 TODOs for CRUD operations (tracker.py)
- Net Worth: 2 TODOs for snapshots storage (ease.py)
- Goals: 1 TODO for goal retrieval (add.py)
- Categorization: 1 TODO for LLM cost tracking (llm_layer.py)
- Recurring: 1 TODO for transaction retrieval (add.py)

## Critical Question: Should fin-infra Own Database Tables?

### Analysis

**fin-infra is a LIBRARY, not an APPLICATION**

Key characteristics:
- fin-infra provides **financial primitives** (banking connections, market data, calculations)
- fin-infra is **provider-agnostic** (Plaid/Teller for banking, Alpaca/IB for brokerage)
- fin-infra is designed to be **reused across MANY applications** (personal finance, wealth management, banking apps)
- fin-infra is installed as a **dependency** via `poetry add fin-infra`

**Precedent: How do other infrastructure libraries handle persistence?**

1. **stripe-python**: NO database tables
   - Provides API client for Stripe
   - Applications store Stripe IDs in their own DB schema
   - Library is stateless

2. **plaid-python**: NO database tables
   - Provides API client for Plaid
   - Applications store access tokens in their own DB
   - Library is stateless

3. **svc-infra auth module**: YES, provides models
   - BUT: svc-infra is a **backend framework**, not a library
   - Provides `User`, `Session` models via ModelBase
   - Applications extend or use as-is
   - Has CLI: `setup-and-migrate` to run migrations

4. **svc-infra payments module**: YES, provides models
   - Same pattern: framework-level persistence
   - Provides `PayCustomer`, `PayIntent`, `LedgerEntry` models
   - Applications can use directly or extend

## Decision Framework

### Option 1: ❌ fin-infra Owns Database Tables (NOT RECOMMENDED)

**Approach**: Create SQLAlchemy models using `svc_infra.db.sql.base.ModelBase` in fin-infra.

**Problems**:
1. **Dependency Hell**: fin-infra would require applications to:
   - Install svc-infra (adds ~50 dependencies)
   - Run `svc-infra setup-and-migrate` with fin-infra models
   - Manage Alembic migrations for fin-infra schema changes
   
2. **Schema Lock-in**: All applications forced to use exact same schema
   - Personal finance app needs different budget fields than business app
   - Wealth management app needs different goal tracking than banking app
   - No flexibility for application-specific requirements

3. **Multi-tenancy Conflicts**: 
   - Some apps are single-tenant (personal finance)
   - Some are multi-tenant SaaS (business budgeting platform)
   - fin-infra can't design schema for both

4. **Version Coupling**:
   - fin-infra schema changes require coordinated migrations
   - Breaking changes impact ALL applications
   - Rollback becomes complex

5. **Database Driver Conflicts**:
   - App uses PostgreSQL, fin-infra assumes SQLite?
   - App uses async drivers, fin-infra uses sync?
   - Impossible to satisfy all use cases

**When this WOULD make sense**:
- If fin-infra were a **backend framework** like Django/Rails (it's not)
- If fin-infra targeted a **single application type** (it doesn't)
- If fin-infra provided a **complete backend** (it only provides financial primitives)

### Option 2: ✅ Applications Own Schema, fin-infra Provides Templates (RECOMMENDED)

**Approach**: fin-infra stays **stateless** and provides **scaffolding tools** for applications.

**Benefits**:
1. **Zero Database Dependency**: fin-infra remains lightweight
2. **Application Flexibility**: Each app designs schema for their needs
3. **Clean Separation**: Library provides logic, apps handle persistence
4. **No Migration Coupling**: fin-infra updates don't break apps
5. **Provider-Agnostic**: Works with any DB (Postgres, MySQL, MongoDB, SQLite)

**Implementation**:

#### A. Provide Pydantic Models Only (Current State)
```python
# fin_infra/budgets/models.py (KEEP AS-IS)
from pydantic import BaseModel

class Budget(BaseModel):
    """Pure data model - no database binding"""
    id: str
    user_id: str
    name: str
    type: BudgetType
    categories: dict[str, float]
```

#### B. Provide SQLAlchemy Templates (NEW)
```python
# fin_infra/budgets/templates/sqlalchemy_template.py
"""
SQLAlchemy model template for budgets.

Applications should COPY this file and customize for their needs.
DO NOT import directly - this is a TEMPLATE, not a model.

Usage:
    1. Copy to your app: cp fin_infra/budgets/templates/sqlalchemy_template.py app/models/budget.py
    2. Customize fields (add tenant_id, soft_delete, etc.)
    3. Use with svc-infra: ModelBase for migrations
    4. Generate migration: svc-infra revision -m "add budgets"
"""

from sqlalchemy import String, JSON, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
# from svc_infra.db.sql.base import ModelBase  # Uncomment when copying to your app

class BudgetModel:  # Change to ModelBase when copying
    """Template SQLAlchemy model for budgets.
    
    CUSTOMIZE for your application:
    - Add tenant_id for multi-tenancy
    - Add deleted_at for soft deletes
    - Add custom indexes
    - Add foreign keys to your User model
    """
    __tablename__ = "budgets"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # personal, household, business
    period: Mapped[str] = mapped_column(String(32), nullable=False)  # monthly, yearly
    categories: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"Food": 500.00}
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rollover_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # OPTIONAL: Add for multi-tenancy
    # tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    
    # OPTIONAL: Add for soft deletes
    # deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # OPTIONAL: Add foreign key to your auth.User
    # from svc_infra.db.sql.authref import user_fk_constraint, user_id_type
    # user_id: Mapped[str] = mapped_column(user_id_type(), nullable=False)
    # __table_args__ = (user_fk_constraint("user_id", ondelete="CASCADE"),)
```

#### C. Provide Repository Pattern Template (NEW)
```python
# fin_infra/budgets/templates/repository_template.py
"""
Repository pattern template for budget persistence.

Applications should COPY and CUSTOMIZE this for their needs.

Usage:
    1. Copy to your app: cp fin_infra/budgets/templates/repository_template.py app/repositories/budget.py
    2. Import your SQLAlchemy model
    3. Customize queries for your schema
    4. Use with fin_infra.budgets.BudgetTracker as storage backend
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fin_infra.budgets.models import Budget  # Pydantic model
# from app.models.budget import BudgetModel  # Your SQLAlchemy model

class BudgetRepository:
    """Repository for budget persistence.
    
    CUSTOMIZE:
    - Add tenant filtering
    - Add soft delete checks
    - Add custom indexes/queries
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, budget: Budget) -> Budget:
        """Create budget in database."""
        db_budget = BudgetModel(
            id=budget.id,
            user_id=budget.user_id,
            name=budget.name,
            type=budget.type.value,
            period=budget.period.value,
            categories=budget.categories,
            start_date=budget.start_date,
            end_date=budget.end_date,
            rollover_enabled=budget.rollover_enabled,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
        )
        self.session.add(db_budget)
        await self.session.commit()
        await self.session.refresh(db_budget)
        return self._to_pydantic(db_budget)
    
    async def get(self, budget_id: str) -> Optional[Budget]:
        """Get budget by ID."""
        stmt = select(BudgetModel).where(BudgetModel.id == budget_id)
        result = await self.session.execute(stmt)
        db_budget = result.scalars().first()
        return self._to_pydantic(db_budget) if db_budget else None
    
    async def list(self, user_id: str, type: Optional[str] = None) -> list[Budget]:
        """List budgets for user."""
        stmt = select(BudgetModel).where(BudgetModel.user_id == user_id)
        if type:
            stmt = stmt.where(BudgetModel.type == type)
        result = await self.session.execute(stmt)
        return [self._to_pydantic(db) for db in result.scalars()]
    
    def _to_pydantic(self, db_budget: BudgetModel) -> Budget:
        """Convert SQLAlchemy model to Pydantic."""
        return Budget(
            id=db_budget.id,
            user_id=db_budget.user_id,
            name=db_budget.name,
            type=db_budget.type,
            period=db_budget.period,
            categories=db_budget.categories,
            start_date=db_budget.start_date,
            end_date=db_budget.end_date,
            rollover_enabled=db_budget.rollover_enabled,
            created_at=db_budget.created_at,
            updated_at=db_budget.updated_at,
        )
```

#### D. Provide CLI Scaffolding Tool (NEW - Following svc-infra Pattern)

**Pattern Reference**: `svc-infra/src/svc_infra/cli/cmds/db/sql/sql_scaffold_cmds.py`

**Key Implementation Details from svc-infra**:
- Uses **Typer** for CLI with **click.Choice()** for enum validation
- Template files in `templates/` subdirectories (`.tmpl` extension)
- Template engine: `importlib.resources.files()` + `string.Template.safe_substitute()`
- Variable substitution: `${Entity}`, `${table_name}`, `${tenant_field}`, `${soft_delete_field}`
- File utilities: `write(dest, content, overwrite)` with parent directory auto-creation
- Overwrite protection: Returns "skipped" if file exists and `--overwrite` not set
- Result tracking: Returns dict with `{"path": str, "action": "wrote|skipped"}`

```python
# fin_infra/cli/cmds/scaffold_cmds.py
"""CLI tool to scaffold models and repositories for applications.

Follows svc-infra's scaffold pattern:
- Template-based generation using importlib.resources
- Typer CLI with options for customization
- Safe substitution with fallback defaults
- Overwrite protection with --overwrite flag

Usage:
    fin-infra scaffold budgets --dest-dir app/models/
    fin-infra scaffold budgets --dest-dir app/models/ --include-tenant --include-soft-delete
    fin-infra scaffold goals --dest-dir app/models/
    fin-infra scaffold net-worth --dest-dir app/models/ --models-filename budget_models.py
    
    # With repository
    fin-infra scaffold budgets --dest-dir app/models/ --with-repository
    
    # Overwrite existing files
    fin-infra scaffold budgets --dest-dir app/models/ --overwrite
"""

from pathlib import Path
from typing import Optional, Literal, Dict, Any
import typer
import click
from fin_infra.utils import render_template, write, ensure_init_py

Domain = Literal["budgets", "goals", "net_worth"]

def cmd_scaffold(
    domain: str = typer.Argument(
        ..., 
        help="Domain to scaffold (budgets, goals, net_worth)",
        click_type=click.Choice(["budgets", "goals", "net_worth"])
    ),
    dest_dir: Path = typer.Option(
        ..., 
        "--dest-dir", 
        resolve_path=True,
        help="Destination directory for generated files"
    ),
    include_tenant: bool = typer.Option(
        False, 
        "--include-tenant/--no-include-tenant",
        help="Add tenant_id field for multi-tenancy"
    ),
    include_soft_delete: bool = typer.Option(
        False, 
        "--include-soft-delete/--no-include-soft-delete",
        help="Add deleted_at field for soft deletes"
    ),
    with_repository: bool = typer.Option(
        True, 
        "--with-repository/--no-with-repository",
        help="Generate repository pattern implementation"
    ),
    overwrite: bool = typer.Option(
        False, 
        "--overwrite/--no-overwrite",
        help="Overwrite existing files"
    ),
    models_filename: Optional[str] = typer.Option(
        None, 
        "--models-filename",
        help="Custom filename for models (default: {domain}.py)"
    ),
    schemas_filename: Optional[str] = typer.Option(
        None,
        "--schemas-filename", 
        help="Custom filename for schemas (default: {domain}_schemas.py)"
    ),
    repository_filename: Optional[str] = typer.Option(
        None, 
        "--repository-filename",
        help="Custom filename for repository (default: {domain}_repository.py)"
    ),
):
    """Scaffold SQLAlchemy models, Pydantic schemas, and repositories for fin-infra domains.
    
    Generated files use svc-infra's ModelBase for Alembic migration compatibility.
    """
    
    if domain == "budgets":
        from fin_infra.scaffold.budgets import scaffold_budgets_core
        res = scaffold_budgets_core(
            dest_dir=dest_dir,
            include_tenant=include_tenant,
            include_soft_delete=include_soft_delete,
            with_repository=with_repository,
            overwrite=overwrite,
            models_filename=models_filename,
            schemas_filename=schemas_filename,
            repository_filename=repository_filename,
        )
    elif domain == "goals":
        from fin_infra.scaffold.goals import scaffold_goals_core
        res = scaffold_goals_core(
            dest_dir=dest_dir,
            include_tenant=include_tenant,
            include_soft_delete=include_soft_delete,
            with_repository=with_repository,
            overwrite=overwrite,
            models_filename=models_filename,
            schemas_filename=schemas_filename,
            repository_filename=repository_filename,
        )
    elif domain == "net_worth":
        from fin_infra.scaffold.net_worth import scaffold_net_worth_core
        res = scaffold_net_worth_core(
            dest_dir=dest_dir,
            include_tenant=include_tenant,
            include_soft_delete=include_soft_delete,
            with_repository=with_repository,
            overwrite=overwrite,
            models_filename=models_filename,
            schemas_filename=schemas_filename,
            repository_filename=repository_filename,
        )
    else:
        typer.echo(f"Unknown domain: {domain}")
        raise typer.Exit(1)
    
    # Display results
    for file_info in res.get("files", []):
        action = file_info.get("action")
        path = file_info.get("path")
        if action == "wrote":
            typer.echo(f"✓ Created: {path}")
        elif action == "skipped":
            reason = file_info.get("reason", "exists")
            typer.echo(f"⊘ Skipped: {path} ({reason})")
    
    return res

def register(app: typer.Typer) -> None:
    """Register scaffold command with CLI app."""
    app.command("scaffold")(cmd_scaffold)
```

```python
# fin_infra/scaffold/budgets.py
"""Scaffold implementation for budgets domain.

Generates:
- SQLAlchemy model with ModelBase (for Alembic migrations)
- Pydantic schemas (Base, Read, Create, Update)
- Repository pattern implementation (optional)
"""

from pathlib import Path
from typing import Optional, Dict, Any
from fin_infra.utils import render_template, write, ensure_init_py

def scaffold_budgets_core(
    *,
    dest_dir: Path,
    include_tenant: bool = False,
    include_soft_delete: bool = False,
    with_repository: bool = True,
    overwrite: bool = False,
    models_filename: Optional[str] = None,
    schemas_filename: Optional[str] = None,
    repository_filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate budget models, schemas, and repository.
    
    Returns:
        dict: {"files": [{"path": str, "action": "wrote|skipped"}]}
    """
    
    # Template variables
    subs = {
        "Entity": "Budget",
        "entity": "budget",
        "table_name": "budgets",
        "tenant_field": _tenant_field() if include_tenant else "",
        "soft_delete_field": _soft_delete_field() if include_soft_delete else "",
        "tenant_arg": ", tenant_id: str" if include_tenant else "",
        "tenant_default": ", tenant_id=None" if include_tenant else "",
    }
    
    # Template directory: fin_infra/budgets/templates/
    tmpl_dir = "fin_infra.budgets.templates"
    
    # Determine filenames
    models_file = models_filename or "budget.py"
    schemas_file = schemas_filename or "budget_schemas.py"
    repo_file = repository_filename or "budget_repository.py"
    
    # Render and write files
    results = []
    
    # 1. SQLAlchemy model
    models_content = render_template(tmpl_dir, "models.py.tmpl", subs)
    models_path = dest_dir / models_file
    results.append(write(models_path, models_content, overwrite))
    
    # 2. Pydantic schemas
    schemas_content = render_template(tmpl_dir, "schemas.py.tmpl", subs)
    schemas_path = dest_dir / schemas_file
    results.append(write(schemas_path, schemas_content, overwrite))
    
    # 3. Repository (optional)
    if with_repository:
        repo_content = render_template(tmpl_dir, "repository.py.tmpl", subs)
        repo_path = dest_dir / repo_file
        results.append(write(repo_path, repo_content, overwrite))
    
    # 4. __init__.py (with re-exports)
    init_content = _generate_init_content(
        models_file=models_file,
        schemas_file=schemas_file,
        repo_file=repo_file if with_repository else None,
    )
    results.append(ensure_init_py(dest_dir, init_content, overwrite))
    
    return {"files": results}

def _tenant_field() -> str:
    """Generate tenant_id field definition."""
    return """
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    """

def _soft_delete_field() -> str:
    """Generate deleted_at field definition."""
    return """
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    """

def _generate_init_content(
    models_file: str, 
    schemas_file: str, 
    repo_file: Optional[str]
) -> str:
    """Generate __init__.py content with re-exports."""
    models_module = models_file.replace(".py", "")
    schemas_module = schemas_file.replace(".py", "")
    
    content = f"""# Budget persistence models (generated by fin-infra scaffold)

from .{models_module} import BudgetModel
from .{schemas_module} import Budget, BudgetCreate, BudgetUpdate, BudgetRead
"""
    
    if repo_file:
        repo_module = repo_file.replace(".py", "")
        content += f"from .{repo_module} import BudgetRepository\n"
    
    content += """
__all__ = [
    "BudgetModel",
    "Budget",
    "BudgetCreate",
    "BudgetUpdate",
    "BudgetRead",
"""
    
    if repo_file:
        content += '    "BudgetRepository",\n'
    
    content += "]\n"
    
    return content
```

```python
# fin_infra/utils.py (NEW - mirrors svc-infra pattern)
"""Utility functions for template rendering and file operations.

Mirrors svc-infra's utils.py for consistency.
"""

from pathlib import Path
from string import Template as _T
from typing import Any, Dict, Optional
import importlib.resources as pkg

def render_template(tmpl_dir: str, name: str, subs: Optional[Dict[str, Any]] = None) -> str:
    """Load template from package resources and substitute variables.
    
    Args:
        tmpl_dir: Package path (e.g., 'fin_infra.budgets.templates')
        name: Template filename (e.g., 'models.py.tmpl')
        subs: Variables to substitute (e.g., {'Entity': 'Budget'})
    
    Returns:
        Rendered template string
    
    Example:
        >>> render_template('fin_infra.budgets.templates', 'models.py.tmpl', {'Entity': 'Budget'})
        'class Budget(ModelBase): ...'
    """
    subs = subs or {}
    txt = pkg.files(tmpl_dir).joinpath(name).read_text(encoding="utf-8")
    return _T(txt).safe_substitute(subs)

def write(dest: Path, content: str, overwrite: bool = False) -> Dict[str, Any]:
    """Write content to file with overwrite protection.
    
    Args:
        dest: Destination file path
        content: Content to write
        overwrite: If True, overwrite existing files
    
    Returns:
        dict: {"path": str, "action": "wrote|skipped", "reason": str (optional)}
    
    Example:
        >>> write(Path("app/models/budget.py"), "class Budget: ...", overwrite=False)
        {"path": "app/models/budget.py", "action": "wrote"}
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    if dest.exists() and not overwrite:
        return {
            "path": str(dest),
            "action": "skipped",
            "reason": "exists (use --overwrite to replace)"
        }
    
    dest.write_text(content, encoding="utf-8")
    return {"path": str(dest), "action": "wrote"}

def ensure_init_py(
    dir_path: Path, 
    content: str, 
    overwrite: bool = False
) -> Dict[str, Any]:
    """Create __init__.py file with optional re-exports.
    
    Args:
        dir_path: Directory for __init__.py
        content: Content to write
        overwrite: If True, overwrite existing file
    
    Returns:
        dict: Same format as write()
    """
    return write(dir_path / "__init__.py", content, overwrite)
```


#### E. Provide Documentation (NEW)
```markdown
# docs/persistence.md

## How to Add Persistence to fin-infra Features

fin-infra is a stateless library. Applications are responsible for persistence.

### Quick Start

1. **Choose your domain**: budgets, goals, net-worth, etc.

2. **Generate models**:
   ```bash
   fin-infra scaffold budgets --output app/models/ --with-tenancy
   ```

3. **Customize schema**:
   ```python
   # app/models/budget.py (generated)
   class BudgetModel(ModelBase):  # Uses svc-infra
       __tablename__ = "budgets"
       # ... customize fields
   ```

4. **Generate migration**:
   ```bash
   svc-infra revision -m "add budgets table"
   svc-infra upgrade head
   ```

5. **Create repository**:
   ```python
   from app.repositories.budget import BudgetRepository
   
   @router.post("/budgets")
   async def create_budget(budget: Budget, session: AsyncSession):
       repo = BudgetRepository(session)
       return await repo.create(budget)
   ```

### Why This Approach?

- **Flexibility**: Each app designs schema for their needs
- **No Lock-in**: Choose any database (Postgres, MySQL, MongoDB)
- **Clean Separation**: fin-infra provides logic, you own data
- **Testability**: Easy to mock persistence layer
```

## Implementation Plan

### Phase 1: Document Current State ✅ (COMPLETED)
1. ✅ Create presistence-strategy.md (this document) at `src/fin_infra/docs/`
2. ✅ Document svc-infra scaffold pattern analysis
3. ✅ Define concrete CLI structure following Typer conventions
4. Next: Add docs/persistence.md with migration guide
5. Next: Update README with "Persistence" section

### Phase 2: Create Utility Infrastructure (NEXT - 2-4 hours)
**Goal**: Set up core scaffolding utilities mirroring svc-infra pattern

**Tasks**:
1. **Create `src/fin_infra/utils.py`** (NEW):
   - `render_template()`: Load `.tmpl` files via importlib.resources
   - `write()`: File writing with overwrite protection
   - `ensure_init_py()`: Generate __init__.py with re-exports
   - Copy implementation from svc-infra with fin-infra adjustments

2. **Create `src/fin_infra/scaffold/__init__.py`** (NEW):
   - Package marker for scaffold modules
   - Re-export core functions for convenience

3. **Test utilities**:
   ```bash
   pytest tests/unit/test_utils.py -v
   ```

**Success Criteria**:
- `render_template()` loads templates from package resources
- `write()` creates parent directories automatically
- `write()` skips existing files when `overwrite=False`
- All unit tests pass

### Phase 3: Create Budgets Templates (NEXT - 4-6 hours)
**Goal**: First complete domain scaffold with `.tmpl` files

**Directory Structure**:
```
src/fin_infra/budgets/templates/
├── models.py.tmpl           # SQLAlchemy model with ModelBase
├── schemas.py.tmpl          # Pydantic schemas (Base/Read/Create/Update)
├── repository.py.tmpl       # Repository pattern with async methods
└── README.md                # Template usage guide
```

**Tasks**:
1. **Create `models.py.tmpl`** (150 lines estimated):
   - Base on svc-infra's entity template
   - Budget-specific fields: user_id, name, type, period, categories (JSON), start_date, end_date, rollover_enabled
   - Variables: `${Entity}`, `${table_name}`, `${tenant_field}`, `${soft_delete_field}`
   - Use ModelBase from svc-infra for Alembic discovery
   - Add unique index on (user_id, name) or (tenant_id, user_id, name)
   - Include budget-specific validation methods

2. **Create `schemas.py.tmpl`** (100 lines estimated):
   - BudgetBase, BudgetRead, BudgetCreate, BudgetUpdate
   - Include BudgetType, BudgetPeriod enums from fin_infra.budgets.models
   - Conditional `${tenant_field}` for multi-tenancy
   - Use ConfigDict(from_attributes=True) for ORM mode

3. **Create `repository.py.tmpl`** (200 lines estimated):
   - BudgetRepository class with async methods
   - CRUD: create(), get(), list(), update(), delete()
   - Budget-specific: get_by_period(), get_active(), get_by_type()
   - Include _to_pydantic() helper to convert SQLAlchemy → Pydantic
   - Docstrings with usage examples

4. **Create `README.md`**:
   - Template variable reference
   - Customization guide
   - Integration with svc-infra migrations
   - Example usage

**Success Criteria**:
- Templates render without errors
- All `${variables}` have sensible defaults
- Templates produce valid Python code
- Manual test: Copy output to test app, run mypy + flake8

### Phase 4: Implement Budgets Scaffold Function (2-3 hours)
**Goal**: Core scaffold logic for budgets domain

**Tasks**:
1. **Create `src/fin_infra/scaffold/budgets.py`**:
   - `scaffold_budgets_core()` with 8 parameters
   - Load templates from `fin_infra.budgets.templates`
   - Substitute variables based on flags
   - Write models, schemas, repository, __init__.py
   - Return dict with file paths and actions

2. **Create unit tests** `tests/unit/scaffold/test_budgets_scaffold.py`:
   - Test variable substitution
   - Test conditional field inclusion (tenant_id, deleted_at)
   - Test overwrite protection
   - Test __init__.py generation
   - Test with/without repository flag

**Success Criteria**:
- `scaffold_budgets_core()` generates 3-4 files
- Files pass mypy type checking
- All unit tests pass (>90% coverage)

### Phase 5: Create CLI Commands (2-3 hours)
**Goal**: User-facing CLI for scaffold commands

**Tasks**:
1. **Create `src/fin_infra/cli/cmds/scaffold_cmds.py`**:
   - `cmd_scaffold()` main command with 9 parameters
   - Use Typer with click.Choice for domain validation
   - Boolean flags: --include-tenant/--no-include-tenant, --include-soft-delete/--no-include-soft-delete
   - Optional: --models-filename, --schemas-filename, --repository-filename
   - `register(app)` function to attach to CLI

2. **Register in main CLI** `src/fin_infra/cli/__init__.py`:
   - Import scaffold_cmds
   - Call scaffold_cmds.register(app)

3. **Test CLI**:
   ```bash
   fin-infra scaffold budgets --dest-dir /tmp/test --include-tenant
   ls -la /tmp/test/
   python -m py_compile /tmp/test/*.py
   ```

**Success Criteria**:
- `fin-infra scaffold --help` shows command
- Command generates files to specified directory
- Generated files are valid Python (no syntax errors)
- --overwrite flag works correctly

### Phase 6: Goals and Net Worth Domains (6-8 hours)
**Goal**: Replicate pattern for remaining domains

**Tasks**:
1. **Goals templates** `src/fin_infra/goals/templates/`:
   - models.py.tmpl: user_id, name, target_amount, current_amount, target_date, status
   - schemas.py.tmpl: GoalBase/Read/Create/Update with GoalStatus enum
   - repository.py.tmpl: CRUD + get_active(), get_by_status()

2. **Goals scaffold** `src/fin_infra/scaffold/goals.py`:
   - `scaffold_goals_core()` matching budgets pattern

3. **Net Worth templates** `src/fin_infra/net_worth/templates/`:
   - models.py.tmpl: user_id, snapshot_date, total_assets, total_liabilities, net_worth, accounts_data (JSON)
   - schemas.py.tmpl: NetWorthSnapshotBase/Read/Create
   - repository.py.tmpl: CRUD + get_by_date_range(), get_latest()

4. **Net Worth scaffold** `src/fin_infra/scaffold/net_worth.py`:
   - `scaffold_net_worth_core()` matching pattern

5. **Update CLI** to support all three domains

**Success Criteria**:
- All three domains scaffold successfully
- CLI supports all domains via --domain flag
- All unit tests pass
- Documentation updated

### Phase 7: Update TODO Comments (1-2 hours)
**Goal**: Replace misleading TODOs with scaffold references

**Files to Update**:
1. **`src/fin_infra/budgets/tracker.py`** (6 TODOs):
   ```python
   # OLD: # TODO: Store in SQL database
   # NEW:
   # Persistence: Applications own database schema (fin-infra is a stateless library).
   # Generate models/schemas/repository: fin-infra scaffold budgets --dest-dir app/models/
   # See docs/persistence.md for full guide.
   # In-memory storage used for testing/examples.
   ```

2. **`src/fin_infra/net_worth/ease.py`** (2 TODOs):
   ```python
   # Persistence: fin-infra scaffold net-worth --dest-dir app/models/
   # See docs/persistence.md for snapshot storage patterns.
   ```

3. **`src/fin_infra/goals/add.py`** (1 TODO):
   ```python
   # Persistence: fin-infra scaffold goals --dest-dir app/models/
   ```

4. **`src/fin_infra/categorization/llm_layer.py`** (1 TODO):
   ```python
   # Cost tracking: Use svc-infra.cache (Redis), not database persistence.
   # from svc_infra.cache import cache_write
   ```

**Success Criteria**:
- All 11 TODOs updated with clear guidance
- No confusion about persistence ownership
- References to scaffold command and docs

### Phase 8: Documentation and Examples (4-6 hours)
**Goal**: Comprehensive guide for developers

**Tasks**:
1. **Create `docs/persistence.md`**:
   - Why fin-infra is stateless
   - When to use scaffold vs manual templates
   - Step-by-step guide: scaffold → customize → migrate
   - Integration with svc-infra ModelBase and Alembic
   - Multi-tenancy patterns
   - Soft delete patterns
   - Testing strategies

2. **Update `README.md`**:
   - Add "Persistence" section with quick example
   - Link to docs/persistence.md
   - Show scaffold command usage

3. **Create `examples/budgets_with_persistence/`**:
   - Full example app using svc-infra + fin-infra
   - Generated models from scaffold
   - Alembic migration
   - API endpoints with repository pattern
   - Tests with pytest + database fixtures

**Success Criteria**:
- Clear documentation for all scaffold features
- Working example app developers can copy
- README updated with persistence guidance

### Phase 9: Testing and Quality Gates (2-3 hours)
**Goal**: Ensure production readiness

**Tasks**:
1. **Unit tests** (target >90% coverage):
   - Test all scaffold functions
   - Test template rendering
   - Test CLI commands
   - Test utils (render_template, write, ensure_init_py)

2. **Integration tests**:
   - Scaffold → mypy → pytest on generated code
   - Test with actual database (svc-infra ModelBase)
   - Test with multi-tenancy flags
   - Test with soft delete flags

3. **Acceptance tests**:
   - Generate budgets scaffold
   - Create Alembic migration: `svc-infra revision -m "add budgets"`
   - Run migration: `svc-infra upgrade head`
   - Use repository in API endpoint
   - Verify CRUD operations work

4. **Quality checks**:
   ```bash
   ruff format && ruff check
   mypy src/fin_infra/scaffold/
   pytest tests/ -q --cov=fin_infra.scaffold --cov-report=term-missing
   ```

**Success Criteria**:
- All tests pass (unit + integration + acceptance)
- Code coverage >90% for scaffold module
- No type errors from mypy
- No lint errors from ruff

### Phase 10: Release and Communication (1-2 hours)
**Goal**: Ship scaffold feature to users

**Tasks**:
1. **Update CHANGELOG.md**:
   - New feature: Scaffold CLI for persistence templates
   - Breaking changes: None (net new feature)
   - Migration guide: How to adopt scaffold for existing projects

2. **Release notes**:
   - Announce scaffold feature
   - Link to docs/persistence.md
   - Show example usage

3. **Update copilot-instructions.md**:
   - Add scaffold workflow to agent expectations
   - Document template structure
   - Add quality gates for template changes

**Success Criteria**:
- Feature documented in CHANGELOG
- Users understand how to adopt scaffold
- Agent knows to use scaffold pattern for future domains

## Exceptions: When fin-infra SHOULD Use Database

### 1. Caching (via svc-infra.cache)
- **Use Case**: LLM cost tracking, market data caching
- **Why**: Temporary data, not application state
- **Implementation**: Use svc-infra Redis cache, not database
```python
from svc_infra.cache import cache_read, cache_write

@cache_read(ttl=3600)
async def get_llm_costs(user_id: str) -> float:
    # Calculate from Redis cache
    pass
```

### 2. Provider Tokens (Application Responsibility)
- **Use Case**: Plaid access tokens, Alpaca API keys
- **Why**: Security-sensitive, application-specific
- **Implementation**: Applications store in their own User model
```python
class User(ModelBase):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    plaid_access_token: Mapped[Optional[str]] = mapped_column(String(255))  # Encrypted
    alpaca_api_key: Mapped[Optional[str]] = mapped_column(String(255))  # Encrypted
```

## Decision Summary

✅ **RECOMMENDED APPROACH**: Option 2 - Applications Own Schema, fin-infra Provides Templates

**Rationale**:
1. fin-infra is a **library**, not a framework - should stay stateless
2. Applications have diverse schema needs - templates provide flexibility
3. Follows industry precedent (stripe-python, plaid-python are stateless)
4. Clean separation of concerns - library provides logic, apps handle data
5. No version coupling - fin-infra updates don't require migrations
6. Works with any database - Postgres, MySQL, MongoDB, etc.

**Action Items**:
1. Document persistence strategy (this document)
2. Update TODO comments to clarify in-memory is intentional
3. Provide SQLAlchemy templates for common domains
4. Add scaffolding CLI in future release
5. Create example app showing full integration

**What NOT to Do**:
- ❌ Don't create ModelBase models in fin-infra
- ❌ Don't add database dependencies to fin-infra
- ❌ Don't create Alembic migrations in fin-infra
- ❌ Don't force applications to use specific schema

**What TO Do**:
- ✅ Keep Pydantic models (stateless, validation only)
- ✅ Provide SQLAlchemy templates (copy-paste, customize)
- ✅ Document repository pattern examples
- ✅ Use svc-infra.cache for temporary data (not DB)
- ✅ Let applications own their persistence layer
