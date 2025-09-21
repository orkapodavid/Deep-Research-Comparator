.PHONY: help install format lint type-check check all clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install development dependencies
	pip install -r master_requirements.txt

format:  ## Format code with black and isort
	black .
	isort .

lint:  ## Run flake8 linter
	flake8 .

autofix:  ## Auto-fix common flake8 issues
	# Remove trailing whitespace
	find . -name "*.py" -exec sed -i '' 's/[[:space:]]*$$//' {} +
	# Run autopep8 to fix basic style issues
	autopep8 --in-place --aggressive --aggressive --recursive .

type-check:  ## Run mypy type checker
	mypy .

check: lint type-check  ## Run all checks (lint + type-check)

all: format autofix check  ## Format code, auto-fix issues, and run all checks

clean:  ## Clean cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Individual service commands
format-app:  ## Format only the app service
	black app/
	isort app/

format-simple:  ## Format only the Simple_DeepResearch_server
	black Simple_DeepResearch_server/
	isort Simple_DeepResearch_server/

format-gpt:  ## Format only the gpt_researcher_server
	black gpt_researcher_server/
	isort gpt_researcher_server/

format-perplexity:  ## Format only the perplexity_server
	black perplexity_server/
	isort perplexity_server/

lint-app:  ## Lint only the app service
	flake8 app/

lint-simple:  ## Lint only the Simple_DeepResearch_server
	flake8 Simple_DeepResearch_server/

lint-gpt:  ## Lint only the gpt_researcher_server
	flake8 gpt_researcher_server/

lint-perplexity:  ## Lint only the perplexity_server
	flake8 perplexity_server/

# Pre-commit hooks
install-hooks:  ## Install pre-commit hooks
	pre-commit install

run-hooks:  ## Run pre-commit hooks on all files
	pre-commit run --all-files