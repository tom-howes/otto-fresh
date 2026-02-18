@echo off
echo Setting up environment files...
echo Make sure you're authenticated: gcloud auth login
echo.

REM Fetch secrets
echo Fetching secrets from GCP Secret Manager...

for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-app-id') do set GITHUB_APP_ID=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-client-id') do set GITHUB_CLIENT_ID=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-client-secret') do set GITHUB_CLIENT_SECRET=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-webhook-secret') do set GITHUB_WEBHOOK_SECRET=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=jwt-secret-key') do set JWT_SECRET_KEY=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=firebase-api-key') do set FIREBASE_API_KEY=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=gemini-api-key') do set GEMINI_API_KEY=%%i

REM Create backend/.env
echo Creating backend/.env...
(
echo GCP_PROJECT_ID=otto-pm
echo REGION=us-east1
echo GCS_BUCKET_RAW=otto-pm-raw-repos
echo GCS_BUCKET_PROCESSED=otto-pm-processed-chunks
echo GCS_BUCKET_ML_ARTIFACTS=otto-pm-ml-artifacts
echo FIREBASE_PROJECT_ID=otto-pm
echo FIREBASE_API_KEY=%FIREBASE_API_KEY%
echo GITHUB_APP_ID=%GITHUB_APP_ID%
echo GITHUB_CLIENT_ID=%GITHUB_CLIENT_ID%
echo GITHUB_CLIENT_SECRET=%GITHUB_CLIENT_SECRET%
echo GITHUB_WEBHOOK_SECRET=%GITHUB_WEBHOOK_SECRET%
echo GITHUB_PRIVATE_KEY_PATH=./github-app-private-key.pem
echo JWT_SECRET_KEY=%JWT_SECRET_KEY%
echo FRONTEND_URL=http://localhost:3000
) > backend\.env

REM Create frontend/.env.local
echo Creating frontend/.env.local...
(
echo NEXT_PUBLIC_API_URL=http://localhost:8000
echo NEXT_PUBLIC_FIREBASE_PROJECT_ID=otto-pm
echo NEXT_PUBLIC_FIREBASE_API_KEY=%FIREBASE_API_KEY%
) > frontend\.env.local

REM Create ingest-service/.env
echo Creating ingest-service/.env...
(
echo GCP_PROJECT_ID=otto-pm
echo REGION=us-east1
echo GCS_BUCKET_RAW=otto-pm-raw-repos
echo GCS_BUCKET_PROCESSED=otto-pm-processed-chunks
echo GEMINI_API_KEY=%GEMINI_API_KEY%
) > ingest-service\.env

REM Download private key
echo.
echo Downloading GitHub private key...
gcloud secrets versions access latest --secret=github-private-key > backend\github-app-private-key.pem

echo.
echo Done! Environment files created:
echo   - backend\.env
echo   - backend\github-app-private-key.pem
echo   - frontend\.env.local
echo   - ingest-service\.env