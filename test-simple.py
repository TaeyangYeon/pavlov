#!/usr/bin/env python3

import os
import sys

# Set up environment variables for testing
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://pavlov_user:changeme@localhost:5432/pavlov"
os.environ["DATABASE_TEST_URL"] = "postgresql+asyncpg://pavlov_user:changeme@localhost:5433/pavlov_test"
os.environ["POSTGRES_USER"] = "pavlov_user"
os.environ["POSTGRES_PASSWORD"] = "changeme"
os.environ["POSTGRES_DB"] = "pavlov"
os.environ["POSTGRES_TEST_DB"] = "pavlov_test"
# Remove problematic CORS env var
if "BACKEND_CORS_ORIGINS" in os.environ:
    del os.environ["BACKEND_CORS_ORIGINS"]

# Add backend to Python path
sys.path.insert(0, '/Users/geseuteu/pavlov/backend')

# Now test the app components
try:
    print("🧪 Testing configuration...")
    from app.core.config import get_settings
    settings = get_settings()
    print("✅ Configuration loaded successfully")
    print(f"   - Secret key: {'✓' if settings.SECRET_KEY else '✗'}")
    print(f"   - Database URL: {'✓' if settings.DATABASE_URL else '✗'}")
    
    print("\n🧪 Testing main app...")
    from app.main import app
    print("✅ FastAPI app loaded successfully")
    
    print("\n🧪 Testing database...")
    from app.infra.db.base import engine
    print("✅ Database engine created successfully")
    
    print("\n🎉 All core components loaded successfully!")
    print("Ready to run tests with proper environment setup.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)