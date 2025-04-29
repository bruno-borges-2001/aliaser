.PHONY: install install-dev test lint format clean pre-commit

# Default target
all: lint test

# Install the package
install:
	uv sync

# Run tests with coverage
test:
	pytest --cov=app --cov-report=term-missing

# Run all linting tools
lint: format-check mypy pylint

# Check code formatting with black
format-check:
	black --check app tests

# Format code with black
format:
	black app tests

# Type checking with mypy
mypy:
	mypy app

# Lint with pylint
pylint:
	pylint app tests

# Run pre-commit hooks on all files
pre-commit:
	pre-commit run --all-files

# Clean up build artifacts and cache files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Help target
help:
	@echo "Available targets:"
	@echo "  install      Install the package"
	@echo "  install-dev  Install the package and development dependencies"
	@echo "  test         Run tests with coverage"
	@echo "  lint         Run all linting tools"
	@echo "  format       Format code with black"
	@echo "  clean        Clean build artifacts and caches"
	@echo "  pre-commit   Run pre-commit hooks on all files"
