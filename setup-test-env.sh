#!/bin/bash
set -e

# Generate a secure secret key
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Create .env file with test values
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://pavlov_user:changeme@localhost:5432/pavlov
DATABASE_TEST_URL=postgresql+asyncpg://pavlov_user:changeme@localhost:5433/pavlov_test

# PostgreSQL Settings
POSTGRES_USER=pavlov_user
POSTGRES_PASSWORD=changeme
POSTGRES_DB=pavlov
POSTGRES_TEST_DB=pavlov_test

# Application Configuration
APP_ENV=development
SECRET_KEY=${SECRET_KEY}
DEBUG=true
API_V1_STR=/api/v1

# CORS Settings (comma-separated origins)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
EOF

echo "✅ .env file created with secure secret key"
echo "✅ Ready to run tests!"
echo ""
echo "Next steps:"
echo "1. source venv/bin/activate"
echo "2. cd backend && pytest tests/ -v"