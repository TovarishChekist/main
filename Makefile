.PHONY: help install run test docker-build docker-run clean lint

help:
	@echo "🔐 Advanced Telegram Encryption Bot - Makefile Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make run          - Run bot locally"
	@echo "  make test         - Run all tests"
	@echo "  make test-security - Run security tests only"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run bot in Docker"
	@echo "  make clean        - Clean temporary files"
	@echo "  make lint         - Run code linters"
	@echo "  make check-env    - Check environment configuration"

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

run:
	@echo "🚀 Starting bot..."
	python main.py

test:
	@echo "🧪 Running all tests..."
	pytest tests/ -v --cov=src --cov-report=html

test-security:
	@echo "🛡️ Running security tests..."
	pytest tests/test_security.py -v

test-encryption:
	@echo "🔐 Running encryption tests..."
	pytest tests/test_encryption.py -v

test-key-exchange:
	@echo "🔑 Running key exchange tests..."
	pytest tests/test_key_exchange.py -v

test-signatures:
	@echo "✍️ Running signature tests..."
	pytest tests/test_signatures.py -v

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t telegram-encryption-bot .

docker-run:
	@echo "🐳 Running bot in Docker..."
	docker-compose up -d

docker-stop:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📋 Viewing Docker logs..."
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	@echo "✅ Cleanup complete"

lint:
	@echo "🔍 Running linters..."
	@echo "Checking with flake8..."
	flake8 src/ --max-line-length=100 --ignore=E501,W503 || true
	@echo "Checking with pylint..."
	pylint src/ --max-line-length=100 || true

check-env:
	@echo "✅ Checking environment configuration..."
	@test -f .env && echo "✅ .env file exists" || echo "❌ .env file missing - copy .env.example"
	@grep -q "TELEGRAM_BOT_TOKEN=" .env 2>/dev/null && echo "✅ Bot token configured" || echo "❌ Bot token not set"

setup:
	@echo "🔧 Setting up project..."
	cp .env.example .env
	@echo "✅ .env file created"
	@echo "⚠️  Please edit .env and add your TELEGRAM_BOT_TOKEN"
	mkdir -p logs
	@echo "✅ Logs directory created"

security-audit:
	@echo "🔍 Running security audit..."
	pip install safety bandit
	safety check
	bandit -r src/ -ll

dev-install:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install flake8 pylint black isort safety bandit

format:
	@echo "🎨 Formatting code..."
	black src/ tests/
	isort src/ tests/

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "Main documentation available in:"
	@echo "  - README.md"
	@echo "  - SECURITY.md"
	@echo "  - EXAMPLES.md"

# Quick start
quickstart: setup install
	@echo ""
	@echo "✅ Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env and add your TELEGRAM_BOT_TOKEN"
	@echo "2. Run: make run"
	@echo ""

all: clean install test
	@echo "✅ All tasks completed!"
