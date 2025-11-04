# Contributing to fin-infra

Thank you for contributing to fin-infra! This guide will help you get set up and understand our development workflow.

## Development Setup

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Poetry for dependency management
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/fin-infra
cd fin-infra

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Install pre-commit hooks
poetry run pre-commit install
```

## Quality Gates

### Format
```bash
# Format code with Black
poetry run black . --line-length 100

# Sort imports with isort
poetry run isort . --profile black --line-length 100
```

### Lint
```bash
# Run flake8
poetry run flake8 --select=E,F
```

### Type Check
```bash
# Run mypy
poetry run mypy src
```

### Tests
```bash
# Run unit tests
poetry run pytest -q

# Run with warnings as errors
poetry run pytest -q -W error

# Run acceptance tests (requires env setup)
poetry run pytest -q -m acceptance
```

### Run All Checks
```bash
# Using Makefile
make format    # Format code
make lint      # Lint code
make type      # Type check
make unit      # Unit tests
make test      # All tests
```

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON validation
- Merge conflict detection
- Black formatting
- isort import sorting
- flake8 linting
- mypy type checking

To run manually:
```bash
poetry run pre-commit run --all-files
```

## Project Structure

```
fin-infra/
├── src/fin_infra/          # Source code
│   ├── banking/            # Banking integrations
│   ├── brokerage/          # Brokerage integrations
│   ├── credit/             # Credit score providers
│   ├── markets/            # Market data providers
│   ├── tax/                # Tax data integrations
│   ├── cashflows/          # Financial calculations
│   ├── models/             # Pydantic data models
│   ├── providers/          # Provider implementations
│   ├── utils/              # Utilities and helpers
│   ├── cli/                # CLI commands
│   └── docs/               # Packaged documentation
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── acceptance/         # Acceptance tests
├── examples/               # Example applications
├── docs/                   # Documentation (root level)
└── scripts/                # Utility scripts
```

## Adding a New Provider

### 1. Create Provider Class

```python
# src/fin_infra/providers/banking/my_provider.py
from fin_infra.providers.base import BankingProvider
from fin_infra.models.accounts import Account
from typing import List

class MyBankingProvider(BankingProvider):
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        super().__init__(**kwargs)
    
    async def get_accounts(self, access_token: str) -> List[Account]:
        # Implementation
        pass
    
    async def get_transactions(self, account_id: str) -> List[Transaction]:
        # Implementation
        pass
```

### 2. Add Tests

```python
# tests/unit/test_my_provider.py
import pytest
from fin_infra.providers.banking import MyBankingProvider

@pytest.mark.asyncio
async def test_get_accounts():
    provider = MyBankingProvider(api_key="test_key")
    accounts = await provider.get_accounts("test_token")
    assert len(accounts) > 0
```

### 3. Add Documentation

Create `src/fin_infra/docs/providers/my-provider.md` with usage examples.

### 4. Update Easy Builder

```python
# src/fin_infra/banking/easy.py
def easy_banking(provider: str = "plaid", **kwargs) -> BankingProvider:
    if provider == "my_provider":
        return MyBankingProvider(**kwargs)
    # ...
```

## Testing Guidelines

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Fast execution (< 1 second each)
- No network calls

### Acceptance Tests
- Test against real provider APIs (sandbox)
- Marked with `@pytest.mark.acceptance`
- Require environment variables for credentials
- Run selectively in CI

### Test Structure
```python
import pytest
from fin_infra.banking import easy_banking

@pytest.mark.asyncio
async def test_feature_name():
    # Arrange
    banking = easy_banking()
    
    # Act
    result = await banking.some_method()
    
    # Assert
    assert result is not None
    assert result.property == expected_value
```

## Documentation Standards

### Code Comments
- Use docstrings for all public functions, classes, and modules
- Follow Google style guide for docstrings
- Include type hints in function signatures

```python
def calculate_npv(rate: float, cashflows: List[float]) -> float:
    """Calculate Net Present Value of cashflows.
    
    Args:
        rate: Discount rate as decimal (0.08 for 8%)
        cashflows: List of cashflows (negative for outflows)
    
    Returns:
        Net present value as float
    
    Raises:
        ValueError: If cashflows list is empty
    """
    pass
```

### Markdown Documentation
- Use clear headings and structure
- Include code examples
- Add "Next Steps" links at the end
- Keep examples copy-pasteable

## Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

Example:
```
feat(banking): add support for Teller provider

- Implement TellerBankingProvider class
- Add account and transaction fetching
- Include unit tests and documentation

Closes #123
```

## Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run Quality Gates**
   ```bash
   make format
   make lint
   make type
   make test
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feat/my-feature
   ```

6. **PR Checklist**
   - [ ] All tests pass
   - [ ] Code is formatted (black/isort)
   - [ ] No linting errors (flake8)
   - [ ] No type errors (mypy)
   - [ ] Documentation updated
   - [ ] Commit messages follow convention

## Release Process

Releases are automated via GitHub Actions:

1. Update version in `pyproject.toml`
2. Create release notes in `CHANGELOG.md`
3. Create and push tag:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```
4. CI builds and publishes to PyPI

## Getting Help

- **GitHub Issues**: https://github.com/your-org/fin-infra/issues
- **Discussions**: https://github.com/your-org/fin-infra/discussions
- **Email**: support@your-org.com

## Code of Conduct

Be respectful, inclusive, and collaborative. See `CODE_OF_CONDUCT.md` for details.
