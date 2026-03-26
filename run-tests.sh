#!/bin/bash
set -e

echo "🧪 Running Pavlov Test Suite"
echo "==========================="

# Ensure we're in the project root
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set the Python path to include backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Add backend to sys.path for imports
cd backend

echo "📍 Running from: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"

# Run tests
echo "🔍 Running pytest..."
pytest tests/ -v --cov=app --cov-report=term-missing

echo "✅ Tests completed!"