#!/bin/bash

echo "Setting up environment files..."
echo "Make sure you're authenticated: gcloud auth login"
echo ""

# Create backend/.env
echo "Creating backend/.env..."
cat > backend/.env << EOF
GOOGLE_CLOUD_PROJECT=otto-pm
REGION=northamerica-northeast1
FIRESTORE_DATABASE=(default)
STORAGE_BUCKET=otto-pm-repo-data
VERTEX_AI_LOCATION=northamerica-northeast1
GITHUB_APP_ID=$(gcloud secrets versions access latest --secret=github-app-id)
GITHUB_PRIVATE_KEY_SECRET=projects/otto-pm/secrets/github-private-key/versions/latest
EOF

# Create frontend/.env.local
echo "Creating frontend/.env.local..."
cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_PROJECT_ID=otto-pm
NEXT_PUBLIC_FIREBASE_API_KEY=$(gcloud secrets versions access latest --secret=firebase-api-key)
EOF

echo ""
echo "Done! Environment files created:"
echo "  - backend/.env"
echo "  - frontend/.env.local"