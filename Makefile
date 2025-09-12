# F1 Scuderia Picker Bot - Makefile for Development Tasks

.PHONY: help test test-quick test-full lint format setup clean install run

# Default target
help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Set up development environment"
	@echo "  make test        - Run quick tests"
	@echo "  make test-full   - Run comprehensive test suite"
	@echo "  make lint        - Run code linting"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean up temporary files"
	@echo "  make run         - Run the bot (requires .env file)"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install flake8 black isort bandit safety  # Development tools

# Set up development environment
setup: install
	@echo "Setting up development environment..."
	@echo "1. Create a .env file with your DISCORD_TOKEN"
	@echo "2. Run 'make test' to verify everything works"
	@echo "3. Run 'make run' to start the bot"

# Run quick tests
test:
	@echo "Running quick tests..."
	python run_tests.py

# Run comprehensive test suite
test-full:
	@echo "Running comprehensive test suite..."
	python test_bot.py

# Run both test suites
test-all: test test-full

# Check syntax
syntax:
	@echo "Checking Python syntax..."
	python -m py_compile bot.py
	python -m py_compile seed_database.py
	python -m py_compile test_bot.py
	python -m py_compile run_tests.py

# Run linting
lint:
	@echo "Running code linting..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
format:
	@echo "Formatting code..."
	black .
	isort .

# Security scan
security:
	@echo "Running security scan..."
	bandit -r . -f json -o bandit-report.json
	bandit -r .
	safety check

# Clean up temporary files
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	rm -rf bandit-report.json
	rm -rf *.db-journal
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Run the bot
run:
	@echo "Starting F1 Scuderia Picker Bot..."
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Please create it with DISCORD_TOKEN=your_token"; \
		exit 1; \
	fi
	python bot.py

# Development workflow
dev: clean setup test-all lint
	@echo "Development environment ready!"

# CI workflow
ci: syntax test-all security lint
	@echo "All CI checks passed!"

# Show test coverage (if coverage.py is installed)
coverage:
	@echo "Running test coverage analysis..."
	@if command -v coverage >/dev/null 2>&1; then \
		coverage run test_bot.py; \
		coverage report; \
		coverage html; \
		echo "Coverage report generated in htmlcov/"; \
	else \
		echo "Coverage.py not installed. Run: pip install coverage"; \
	fi
