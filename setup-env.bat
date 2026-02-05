@echo off
echo Setting up environment files...

echo Fetching secrets from GCP Secret Manager...
echo Make sure you're authenticated: gcloud auth login

REM Create backend/.env
echo Creating backend/.env...
(
echo GOOGLE_CLOUD_PROJECT=otto-pm
echo REGION=northamerica-northeast1
echo FIRESTORE_DATABASE=(default)
echo STORAGE_BUCKET=otto-pm-repo-data
echo VERTEX_AI_LOCATION=northamerica-northeast1
) > backend\.env

REM Append GitHub App ID
echo Fetching GitHub App ID...
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=github-app-id') do set GITHUB_APP_ID=%%i
echo GITHUB_APP_ID=%GITHUB_APP_ID% >> backend\.env
echo GITHUB_PRIVATE_KEY_SECRET=projects/otto-pm/secrets/github-private-key/versions/latest >> backend\.env

REM Create frontend/.env.local
echo Creating frontend/.env.local...
(
echo NEXT_PUBLIC_API_URL=http://localhost:8000
echo NEXT_PUBLIC_FIREBASE_PROJECT_ID=otto-pm
) > frontend\.env.local

REM Append Firebase API Key
echo Fetching Firebase API Key...
for /f "delims=" %%i in ('gcloud secrets versions access latest --secret=firebase-api-key') do set FIREBASE_API_KEY=%%i
echo NEXT_PUBLIC_FIREBASE_API_KEY=%FIREBASE_API_KEY% >> frontend\.env.local

echo.
echo Done! Environment files created:
echo   - backend\.env
echo   - frontend\.env.local