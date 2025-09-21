# Backend Development Tools

This document describes the Python type checking and formatting tools available for the backend services.

## Installed Tools

- **Black**: Code formatter that enforces consistent style
- **isort**: Import statement organizer
- **flake8**: Code linter that checks for style and programming errors
- **mypy**: Static type checker
- **pre-commit**: Git hooks framework for automated checks

## Quick Start

### 1. Install Development Dependencies

```bash
# Install all dependencies including development tools
pip install -r master_requirements.txt
```

### 2. Format Your Code

```bash
# Format all Python files
make format

# Or run individually
black .
isort .
```

### 3. Check Code Quality

```bash
# Run all checks (lint + type-check)
make check

# Or run individually
make lint        # Run flake8
make type-check  # Run mypy
```

### 4. Set Up Pre-commit Hooks (Recommended)

```bash
# Install pre-commit hooks
make install-hooks

# Now every commit will automatically run formatting and checks
```

## Available Make Commands

```bash
make help          # Show all available commands
make install       # Install development dependencies
make format        # Format code with black and isort
make lint          # Run flake8 linter
make type-check    # Run mypy type checker
make check         # Run all checks (lint + type-check)
make all           # Format code and run all checks
make clean         # Clean cache files

# Service-specific commands
make format-app         # Format only the app service
make format-simple      # Format only the Simple_DeepResearch_server
make format-gpt         # Format only the gpt_researcher_server
make format-perplexity  # Format only the perplexity_server

make lint-app           # Lint only the app service
make lint-simple        # Lint only the Simple_DeepResearch_server
make lint-gpt           # Lint only the gpt_researcher_server
make lint-perplexity    # Lint only the perplexity_server

# Pre-commit commands
make install-hooks      # Install pre-commit hooks
make run-hooks         # Run pre-commit hooks on all files
```

## Configuration

### Black Configuration
- Line length: 88 characters
- Target Python version: 3.12
- Configuration in `pyproject.toml`

### isort Configuration
- Profile: black (compatible with Black)
- Multi-line output style: 3
- Configuration in `pyproject.toml`

### flake8 Configuration
- Max line length: 88 characters
- Ignores E203, W503 (conflicts with Black)
- Configuration in `pyproject.toml`

### mypy Configuration
- Python version: 3.12
- Strict type checking enabled
- Ignores missing imports for third-party libraries
- Configuration in `pyproject.toml`

## Integration with Docker

The development tools are included in the requirements files but won't affect production Docker images since they're marked as development dependencies.

## Best Practices

1. **Before committing**: Always run `make all` to ensure code is formatted and passes checks
2. **Use pre-commit hooks**: Run `make install-hooks` to automatically format and check code on every commit
3. **Service-specific work**: Use service-specific commands (e.g., `make format-app`) when working on a single service
4. **Type hints**: Add type hints to all new functions and methods for better code quality

## Troubleshooting

### Common Issues

1. **Import errors with mypy**: Some third-party libraries don't have type stubs. These are configured to be ignored in `pyproject.toml`

2. **Long lines**: Black will automatically format long lines, but sometimes manual breaking is needed for readability

3. **Import order**: isort might conflict with existing import order. Run `isort .` to fix automatically

### VS Code Integration

To integrate with VS Code, add these settings to your workspace settings:

```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```