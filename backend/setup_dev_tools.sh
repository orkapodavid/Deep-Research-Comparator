#!/bin/bash

# Backend Development Tools Setup Script
# This script sets up the Python development tools for the backend services

set -e

echo "🚀 Setting up Python development tools for backend services..."

# Check if we're in the backend directory
if [[ ! -f "master_requirements.txt" ]]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install -r master_requirements.txt

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

# Run initial formatting and checks
echo "🎨 Running initial code formatting..."
black .
isort .

echo "🔍 Running code quality checks..."
flake8 . || echo "⚠️  Some linting issues found - please review"
mypy . || echo "⚠️  Some type checking issues found - please review"

echo "✅ Development tools setup complete!"
echo ""
echo "📚 Available commands:"
echo "  make help          - Show all available commands"
echo "  make format        - Format code"
echo "  make check         - Run all checks"
echo "  make all           - Format and check code"
echo ""
echo "💡 Tip: Run 'make all' before committing changes"
echo "🔧 See DEV_TOOLS_README.md for detailed documentation"