@echo off
echo Setting up environment files...
echo Make sure you're authenticated: gcloud auth login
echo.

REM Fetch secrets
echo Fetching secrets from GCP Secret Manager...

for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=gemini-api-key 2^>nul') do set GEMINI_API_KEY=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-app-id 2^>nul') do set GITHUB_APP_ID=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-client-id 2^>nul') do set GITHUB_CLIENT_ID=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-client-secret 2^>nul') do set GITHUB_CLIENT_SECRET=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-webhook-secret 2^>nul') do set GITHUB_WEBHOOK_SECRET=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=jwt-secret-key 2^>nul') do set JWT_SECRET_KEY=%%i
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=firebase-api-key 2^>nul') do set FIREBASE_API_KEY=%%i

REM Create .env (shared project root)
echo Creating .env (shared)...
(
echo GCP_PROJECT_ID=otto-pm
echo REGION=us-east1
echo GCS_BUCKET_RAW=otto-pm-raw-repos
echo GCS_BUCKET_PROCESSED=otto-pm-processed-chunks
echo GCS_BUCKET_ML_ARTIFACTS=otto-pm-ml-artifacts
echo FIRESTORE_DATABASE=(default)
echo GEMINI_API_KEY=%GEMINI_API_KEY%
echo ENVIRONMENT=development
echo FRONTEND_URL=http://localhost:3000
) > .\.env

REM Create backend/.env.local
echo Creating backend/.env.local...
(
echo GITHUB_APP_ID=%GITHUB_APP_ID%
echo GITHUB_CLIENT_ID=%GITHUB_CLIENT_ID%
echo GITHUB_CLIENT_SECRET=%GITHUB_CLIENT_SECRET%
echo GITHUB_WEBHOOK_SECRET=%GITHUB_WEBHOOK_SECRET%
echo GITHUB_CALLBACK_URL=http://localhost:8000/auth/github/callback
echo GITHUB_PRIVATE_KEY_PATH=%cd%\backend\github-private-key.pem
echo FIREBASE_CREDENTIALS_PATH=%cd%\backend\firebase-credentials.json
echo FIREBASE_PROJECT_ID=otto-pm
echo JWT_SECRET_KEY=%JWT_SECRET_KEY%
echo PORT=8000
echo HOST=0.0.0.0
) > backend\.env.local

REM Download GitHub private key
echo Fetching GitHub private key...
call gcloud secrets versions access latest --secret=github-private-key > backend\github-private-key.pem

REM Download Firebase credentials
echo Fetching Firebase credentials...
call gcloud secrets versions access latest --secret=firebase-credentials > backend\firebase-credentials.json

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

echo.
echo Done! Environment files created:
echo   - .env (shared project root)
echo   - backend\.env.local
echo   - backend\github-private-key.pem
echo   - backend\firebase-credentials.json
echo   - frontend\.env.local
echo   - ingest-service\.env