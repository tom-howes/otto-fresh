#!/bin/bash
echo "Setting up environment files..."
echo "Make sure you're authenticated: gcloud auth login"
echo ""

# Create otto/.env (shared/project root)
echo "Creating .env (shared)..."
cat > .env << EOF
GCP_PROJECT_ID=otto-pm
REGION=us-east1
GCS_BUCKET_RAW=otto-pm-raw-repos
GCS_BUCKET_PROCESSED=otto-pm-processed-chunks
GCS_BUCKET_ML_ARTIFACTS=otto-pm-ml-artifacts
FIRESTORE_DATABASE=(default)
GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key 2>/dev/null || echo "NOT_SET")
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
EOF

# Create backend/.env.local (backend-specific, secrets)
echo "Creating backend/.env.local..."

# Fetch GitHub private key content (not just the reference)
GITHUB_PRIVATE_KEY=$(gcloud secrets versions access latest --secret=github-private-key)

cat > backend/.env.local << EOF
GITHUB_APP_ID=$(gcloud secrets versions access latest --secret=github-app-id)
GITHUB_CLIENT_ID=$(gcloud secrets versions access latest --secret=github-client-id 2>/dev/null || echo "NOT_SET")
GITHUB_CLIENT_SECRET=$(gcloud secrets versions access latest --secret=github-client-secret 2>/dev/null || echo "NOT_SET")
GITHUB_WEBHOOK_SECRET=$(gcloud secrets versions access latest --secret=github-webhook-secret 2>/dev/null || echo "NOT_SET")
GITHUB_CALLBACK_URL=http://localhost:8000/auth/github/callback
FIREBASE_CREDENTIALS_PATH=$(pwd)/backend/firebase-credentials.json
FIREBASE_PROJECT_ID=otto-pm
JWT_SECRET_KEY=$(gcloud secrets versions access latest --secret=jwt-secret-key)
PORT=8000
HOST=0.0.0.0
EOF

# Write GitHub private key to a file (config.py reads it from disk)
echo "Fetching GitHub private key..."
gcloud secrets versions access latest --secret=github-private-key > backend/github-private-key.pem
echo "GITHUB_PRIVATE_KEY_PATH=$(pwd)/backend/github-private-key.pem" >> backend/.env.local

# Fetch Firebase credentials JSON
echo "Fetching Firebase credentials..."
gcloud secrets versions access latest --secret=firebase-credentials > backend/firebase-credentials.json

# Create frontend/.env.local
echo "Creating frontend/.env.local..."
cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_PROJECT_ID=otto-pm
NEXT_PUBLIC_FIREBASE_API_KEY=${FIREBASE_API_KEY}
EOF

# Create ingest-service/.env
echo "Creating ingest-service/.env..."
cat > ingest-service/.env << EOF
GCP_PROJECT_ID=otto-pm
REGION=us-east1
GCS_BUCKET_RAW=otto-pm-raw-repos
GCS_BUCKET_PROCESSED=otto-pm-processed-chunks
GEMINI_API_KEY=${GEMINI_API_KEY}
EOF

# Download private key
echo ""
echo "Downloading GitHub private key..."
gcloud secrets versions access latest --secret=github-private-key > backend/github-private-key.pem

echo ""
echo "Done! Environment files created:"
echo "  - .env (shared project root)"
echo "  - backend/.env.local (backend secrets)"
echo "  - backend/github-private-key.pem"
echo "  - backend/firebase-credentials.json"
echo "  - frontend/.env.local"