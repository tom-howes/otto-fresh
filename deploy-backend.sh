#!/bin/bash
set -e

echo "🚀 Deploying Backend Service..."

cd backend

gcloud run deploy backend-service \
  --source=. \
  --region=us-east1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --timeout=300 \
  --update-env-vars="GCP_PROJECT_ID=otto-pm" \
  --update-env-vars="GCS_BUCKET_RAW=otto-pm-raw-repos" \
  --update-env-vars="GCS_BUCKET_PROCESSED=otto-pm-processed-chunks" \
  --update-env-vars="INGEST_SERVICE_URL=https://ingest-service-5uvajfblma-ue.a.run.app" \
  --update-env-vars="FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json" \
  --update-env-vars="FIREBASE_PROJECT_ID=otto-pm" \
  --update-env-vars="GITHUB_PRIVATE_KEY_PATH=./github-app-private-key.pem" \
  --update-env-vars="GITHUB_APP_ID=1087451" \
  --update-env-vars="GITHUB_CLIENT_ID=Iv23lilfCBU9PNAJ947B" \
  --update-env-vars="GITHUB_CLIENT_SECRET=37b5fbb7aa38eef30c1402863da466e590577927" \
  --update-env-vars="GITHUB_CALLBACK_URL=https://backend-service-484671782718.us-east1.run.app/auth/github/callback" \
  --update-env-vars="JWT_SECRET_KEY=GZFb01Fvwnc5itGObT_AO61XhJuvW1ZqYqRLn0pPuRs" \
  --update-env-vars="GITHUB_WEBHOOK_SECRET=LZhRUB1hf2MvR0WJuTn-kC1N0PoBSn7HyKcA6raFa0g" \
  --update-env-vars="FRONTEND_URL=https://backend-service-484671782718.us-east1.run.app/"

echo "✅ Backend deployed!"
