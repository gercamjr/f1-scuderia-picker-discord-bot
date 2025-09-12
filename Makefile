# F1 Scuderia Picker Bot - Makefile for Development Tasks

.PHONY: help test test-quick test-full lint format setup clean install run pre-commit ci-setup

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make setup        - Set up development environment"
	@echo "  make pre-commit   - Set up pre-commit hooks"
	@echo "  make ci-setup     - Set up CI/CD and branch protection"
	@echo "  make test         - Run quick tests"
	@echo "  make test-full    - Run comprehensive test suite"
	@echo "  make lint         - Run code linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean up temporary files"
	@echo "  make run          - Run the bot (requires .env file)"

# Install dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Set up development environment
setup: install-dev pre-commit
	@echo "Setting up development environment..."
	@echo "1. Create a .env file with your DISCORD_TOKEN"
	@echo "2. Run 'make test' to verify everything works"
	@echo "3. Run 'make run' to start the bot"
	@echo "4. Pre-commit hooks are now installed"

# Set up pre-commit hooks
pre-commit:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

# Set up CI/CD and branch protection
ci-setup:
	@echo "🔧 Setting up CI/CD and branch protection..."
	@echo ""
	@echo "📋 GitHub Actions workflow is already configured in .github/workflows/test.yml"
	@echo ""
	@echo "🛡️ To set up branch protection, choose one option:"
	@echo ""
	@echo "Option 1 - Using GitHub CLI:"
	@echo "  gh auth login"
	@echo "  gh api repos/gercamjr/f1-scuderia-picker-discord-bot/branches/main/protection \\"
	@echo "    --method PUT \\"
	@echo "    --field required_status_checks='{\"strict\":true,\"contexts\":[\"All Checks Passed ✅\"]}' \\"
	@echo "    --field enforce_admins=true \\"
	@echo "    --field required_pull_request_reviews='{\"required_approving_review_count\":0,\"dismiss_stale_reviews\":true}' \\"
	@echo "    --field restrictions=null"
	@echo ""
	@echo "Option 2 - Manual setup:"
	@echo "  1. Go to GitHub repository settings"
	@echo "  2. Click 'Branches' → 'Add rule'"
	@echo "  3. Set branch name: main"
	@echo "  4. Enable: 'Require status checks to pass before merging'"
	@echo "  5. Select: 'All Checks Passed ✅' as required status check"
	@echo "  6. Save changes"
	@echo ""
	@echo "📖 See BRANCH_PROTECTION.md for detailed instructions"

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
