"""
Configuration loader for ingest-service
Loads shared .env from parent directory + optional local overrides
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# Get paths
INGEST_DIR = Path(__file__).parent
PROJECT_ROOT = INGEST_DIR.parent  # otto/

# 1. Load SHARED .env from project root (otto/.env)
shared_env = PROJECT_ROOT / '.env'
if shared_env.exists():
    load_dotenv(shared_env)
    print(f"✓ Loaded shared config: {shared_env}")
else:
    print(f"⚠️  Shared .env not found at: {shared_env}")
    print(f"   Create it at: {PROJECT_ROOT}/.env")

# 2. Load LOCAL .env.local (optional overrides)
local_env = INGEST_DIR / '.env.local'
if local_env.exists():
    load_dotenv(local_env, override=True)
    print(f"✓ Loaded local overrides: {local_env}")
else:
    print(f"ℹ️  No local overrides (optional)")

# ==================== EXPORT CONFIGURATION ====================

# GCP Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_REGION", "us-central1")
BUCKET_RAW = os.getenv("GCS_BUCKET_RAW")
BUCKET_PROCESSED = os.getenv("GCS_BUCKET_PROCESSED")
BUCKET_TEMP = os.getenv("GCS_BUCKET_TEMP")

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Fallback only, prefer user token

# AI/ML Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "8192"))

# Pipeline Configuration
CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "150"))
OVERLAP = int(os.getenv("DEFAULT_OVERLAP", "10"))
TOP_K = int(os.getenv("DEFAULT_TOP_K", "10"))
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "25"))

# Features
ENABLE_GITHUB_PUSH = os.getenv("ENABLE_GITHUB_PUSH", "true").lower() == "true"
ENABLE_LOCAL_SAVE = os.getenv("ENABLE_LOCAL_SAVE", "true").lower() == "true"

# Output Directories (can be overridden in .env.local)
DOCS_OUTPUT_DIR = os.getenv("DOCS_OUTPUT_DIR", "./docs")
CODE_EDITS_DIR = os.getenv("CODE_EDITS_DIR", "./docs/code_edits")

# Development
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validate required variables
if not PROJECT_ID:
    print("❌ ERROR: GCP_PROJECT_ID not set in .env")
if not BUCKET_RAW:
    print("❌ ERROR: GCS_BUCKET_RAW not set in .env")
if not BUCKET_PROCESSED:
    print("❌ ERROR: GCS_BUCKET_PROCESSED not set in .env")
if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not set - RAG features will not work")