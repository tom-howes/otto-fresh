"""
Backend configuration loader
Loads: otto/.env (shared) + backend/.env.local (backend-specific)
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# Get directories
BACKEND_DIR = Path(__file__).parent.parent  # backend/
PROJECT_ROOT = BACKEND_DIR.parent           # otto/

print(f"Backend dir: {BACKEND_DIR}")
print(f"Project root: {PROJECT_ROOT}")

# 1. Load SHARED .env from project root (otto/.env)
shared_env = PROJECT_ROOT / '.env'
if shared_env.exists():
    load_dotenv(shared_env)
    print(f"✓ Loaded shared config: {shared_env}")
else:
    print(f"❌ ERROR: Shared .env not found at: {shared_env}")
    print(f"   Create it: cp {PROJECT_ROOT}/.env.example {shared_env}")

# 2. Load BACKEND .env.local (overrides shared)
local_env = BACKEND_DIR / '.env.local'
if local_env.exists():
    load_dotenv(local_env, override=True)
    print(f"✓ Loaded backend config: {local_env}")
else:
    print(f"❌ ERROR: Backend .env.local not found at: {local_env}")
    print(f"   This file is REQUIRED for Firebase and JWT config")

# ==================== GITHUB CONFIGURATION ====================
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL")

# Load GitHub private key
if GITHUB_PRIVATE_KEY_PATH and os.path.exists(GITHUB_PRIVATE_KEY_PATH):
    with open(GITHUB_PRIVATE_KEY_PATH, "r") as f:
        GITHUB_PRIVATE_KEY = f.read()
else:
    GITHUB_PRIVATE_KEY = None
    print("❌ ERROR: GitHub private key not found")

# ==================== FIREBASE CONFIGURATION ====================
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

# ==================== JWT CONFIGURATION ====================
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    print("❌ ERROR: JWT_SECRET_KEY not set in backend/.env.local")
    print("   Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")

# ==================== RAG CONFIGURATION (from shared .env) ====================
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_RAW = os.getenv("GCS_BUCKET_RAW")
GCS_BUCKET_PROCESSED = os.getenv("GCS_BUCKET_PROCESSED")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==================== SERVER CONFIGURATION ====================
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
