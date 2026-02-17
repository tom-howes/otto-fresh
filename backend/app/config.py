# backend/app/config.py
"""
Backend configuration loader
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# Get directories
BACKEND_DIR = Path(__file__).parent.parent  # backend/
PROJECT_ROOT = BACKEND_DIR.parent           # otto/

print(f"Backend dir: {BACKEND_DIR}")
print(f"Project root: {PROJECT_ROOT}")

# 1. Load SHARED .env from project root (otto/.env) - ONLY FOR LOCAL
shared_env = PROJECT_ROOT / '.env'
if shared_env.exists():
    load_dotenv(shared_env)
    print(f"✓ Loaded shared config: {shared_env}")
else:
    # In Cloud Run, .env won't exist - env vars come from deployment
    print(f"ℹ️  No shared .env found (expected in Cloud Run)")

# 2. Load BACKEND .env.local (overrides shared) - ONLY FOR LOCAL
local_env = BACKEND_DIR / '.env.local'
if local_env.exists():
    load_dotenv(local_env, override=True)
    print(f"✓ Loaded backend config: {local_env}")
else:
    print(f"ℹ️  No backend .env.local found (expected in Cloud Run)")

# ==================== GITHUB CONFIGURATION ====================
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

if not GITHUB_WEBHOOK_SECRET:
    print("⚠️  WARNING: GITHUB_WEBHOOK_SECRET not set - webhooks will be insecure")

# Load GitHub private key
if GITHUB_PRIVATE_KEY_PATH and os.path.exists(GITHUB_PRIVATE_KEY_PATH):
    with open(GITHUB_PRIVATE_KEY_PATH, "r") as f:
        GITHUB_PRIVATE_KEY = f.read()
else:
    GITHUB_PRIVATE_KEY = None
    print("⚠️  WARNING: GitHub private key not found")

# ==================== FIREBASE CONFIGURATION ====================
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

# ==================== JWT CONFIGURATION ====================
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    print("⚠️  WARNING: JWT_SECRET_KEY not set")

# ==================== RAG CONFIGURATION ====================
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_RAW = os.getenv("GCS_BUCKET_RAW")
GCS_BUCKET_PROCESSED = os.getenv("GCS_BUCKET_PROCESSED")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==================== INGEST SERVICE URL ====================
# CRITICAL: Must have http:// or https:// prefix
INGEST_SERVICE_URL = os.getenv("INGEST_SERVICE_URL", "http://localhost:8081")

# Validate URL format
if INGEST_SERVICE_URL and not INGEST_SERVICE_URL.startswith(("http://", "https://")):
    print(f"❌ ERROR: INGEST_SERVICE_URL must start with http:// or https://")
    print(f"   Current value: {INGEST_SERVICE_URL}")
    INGEST_SERVICE_URL = f"https://{INGEST_SERVICE_URL}"
    print(f"   Auto-corrected to: {INGEST_SERVICE_URL}")

print(f"✓ Ingest service URL: {INGEST_SERVICE_URL}")

# ==================== SERVER CONFIGURATION ====================
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")