#!/bin/bash
set -e

echo "🚀 Deploying Ingest Service..."

cd ingest-service

gcloud run deploy ingest-service \
  --source=. \
  --region=us-east1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --timeout=300 \
  --update-env-vars="GCP_PROJECT_ID=otto-pm" \
  --update-env-vars="GCS_BUCKET_RAW=otto-pm-raw-repos" \
  --update-env-vars="GCS_BUCKET_PROCESSED=otto-pm-processed-chunks"

echo "✅ Ingest service deployed!"
