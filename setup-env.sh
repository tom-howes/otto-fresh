#!/bin/bash

echo "Setting up environment files..."
echo "Make sure you're authenticated: gcloud auth login"
echo ""

# Fetch secrets
echo "Fetching secrets from GCP Secret Manager..."

GITHUB_APP_ID=$(gcloud secrets versions access latest --secret=github-app-id)
GITHUB_CLIENT_ID=$(gcloud secrets versions access latest --secret=github-client-id)
GITHUB_CLIENT_SECRET=$(gcloud secrets versions access latest --secret=github-client-secret)
GITHUB_WEBHOOK_SECRET=$(gcloud secrets versions access latest --secret=github-webhook-secret)
JWT_SECRET_KEY=$(gcloud secrets versions access latest --secret=jwt-secret-key)
FIREBASE_API_KEY=$(gcloud secrets versions access latest --secret=firebase-api-key)
GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)

# Create backend/.env
echo "Creating backend/.env..."
cat > backend/.env << EOF
GCP_PROJECT_ID=otto-pm
REGION=us-east1
GCS_BUCKET_RAW=otto-pm-raw-repos
GCS_BUCKET_PROCESSED=otto-pm-processed-chunks
GCS_BUCKET_ML_ARTIFACTS=otto-pm-ml-artifacts
FIREBASE_PROJECT_ID=otto-pm
FIREBASE_API_KEY=${FIREBASE_API_KEY}
GITHUB_APP_ID=${GITHUB_APP_ID}
GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
GITHUB_PRIVATE_KEY_PATH=./github-app-private-key.pem
JWT_SECRET_KEY=${JWT_SECRET_KEY}
FRONTEND_URL=http://localhost:3000
EOF

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
gcloud secrets versions access latest --secret=github-private-key > backend/github-app-private-key.pem

echo ""
echo "Done! Environment files created:"
echo "  - backend/.env"
echo "  - backend/github-app-private-key.pem"
echo "  - frontend/.env.local"
echo "  - ingest-service/.env"