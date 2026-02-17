# OTTO

**An AI-Powered Project Management Solution with RAG**

Otto is an intelligent project management tool for software teams that connects directly to your GitHub repositories. It uses Retrieval-Augmented Generation (RAG) to understand your codebase and provide contextual Q&A, automated documentation generation, intelligent code completion, and AI-powered code editing — all from a single platform.

---

## Features

### Core RAG Services
- **Q&A Agent** — Ask natural language questions about your codebase and get accurate, context-aware answers with source references
- **Documentation Generator** — Auto-generate API docs, user guides, technical docs, and READMEs from your code
- **Code Completion** — Get intelligent code suggestions based on patterns in your actual codebase
- **Code Editor** — Modify code with natural language instructions, with automatic PR creation

### Pipeline & Infrastructure
- **Automated Ingestion** — Connect a GitHub repo and Otto ingests, chunks, and embeds your code automatically
- **Smart Caching** — Commit tracking ensures re-indexing only happens when new code is pushed
- **Webhook Auto-Sync** — Push to main and embeddings update automatically in the background
- **Login Sync** — Missed updates while logged out are detected and synced on next login
- **Streaming Responses** — Real-time SSE streaming for all RAG services
- **Multi-User Support** — Shared chunk storage with per-user access tracking and preferences

### GitHub Integration
- **OAuth Authentication** — Sign in with GitHub, access private repos
- **GitHub App** — Installation-level access with fine-grained permissions
- **PR Creation** — Code edits and documentation can be pushed as pull requests directly
- **Branch Protection** — Webhook only triggers on the tracked branch

---

## Architecture
```
┌──────────────┐       ┌──────────────────┐       ┌──────────────────────┐
│   Frontend   │──────▶│  Backend Service  │──────▶│   Ingest Service     │
│  (Next.js)   │       │    (FastAPI)      │       │     (FastAPI)        │
└──────────────┘       └──────────────────┘       └──────────────────────┘
                              │                           │
                              │                           │
                       ┌──────┴──────┐            ┌───────┴────────┐
                       │  Firebase   │            │  Google Cloud  │
                       │  Firestore  │            │    Storage     │
                       │  (Users)    │            │  (Raw + Chunks)│
                       └─────────────┘            └───────┬────────┘
                                                          │
                                                  ┌───────┴────────┐
                                                  │   Vertex AI    │
                                                  │  Embeddings +  │
                                                  │  Gemini LLM    │
                                                  └────────────────┘
```

### Service Responsibilities

| Service | Responsibilities |
|---------|-----------------|
| **Frontend** | UI, authentication flow, dashboard, chat interface |
| **Backend** | Auth, user management, access control, user tracking, webhook handling |
| **Ingest Service** | RAG pipeline (ingest → chunk → embed), Q&A, docs, code completion, code editing, vector search |

### Data Flow
```
GitHub Push → Webhook → Backend → Ingest Service → GCS Buckets
     │                                                   │
     │                              Ingest: GitHub API → Raw Bucket
     │                              Chunk:  Tree-sitter → Processed Bucket
     │                              Embed:  Vertex AI  → Processed Bucket (updated)
     │
User Query → Backend (auth) → Ingest Service → Vector Search → Gemini → Response
```

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, React, Tailwind CSS |
| **Backend** | FastAPI, Python 3.11, Firebase Admin |
| **Ingest Service** | FastAPI, Tree-sitter, Vertex AI, Gemini |
| **Database** | Firestore (users), Cloud Storage (code/chunks) |
| **ML/AI** | Vertex AI Embeddings (text-embedding-004), Gemini 1.5 Flash |
| **Auth** | GitHub OAuth, GitHub App, JWT sessions |
| **Infrastructure** | GCP Cloud Run, Artifact Registry, Cloud Build |
| **Dev Tools** | Docker, gcloud CLI, smee.io (webhook dev) |

---

## Project Structure
```
otto/
├── frontend/                  # Next.js web application
│   ├── src/
│   ├── package.json
│   └── ...
│
├── backend/                   # Backend API service
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── config.py         # Environment configuration
│   │   ├── routes/
│   │   │   ├── auth.py       # GitHub OAuth + session management
│   │   │   ├── github.py     # GitHub App installation routes
│   │   │   ├── user.py       # User profile routes
│   │   │   ├── rag.py        # RAG endpoints (proxies to ingest service)
│   │   │   └── webhook.py    # GitHub webhook handler
│   │   ├── clients/
│   │   │   ├── github.py     # GitHub API client (App + OAuth)
│   │   │   ├── firebase.py   # Firestore client
│   │   │   └── ingest_service.py  # HTTP client for ingest service
│   │   ├── dependencies/
│   │   │   └── auth.py       # JWT auth dependency
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic
│   │   ├── types/            # Type definitions
│   │   └── utils/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .gcloudignore
│
├── ingest-service/            # RAG pipeline service
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   └── routes/
│   │       └── pipeline.py   # Pipeline + RAG endpoints
│   ├── src/
│   │   ├── ingestion/
│   │   │   └── github_ingester.py    # GitHub repo → GCS
│   │   ├── chunking/
│   │   │   ├── enhanced_chunker.py   # Semantic code chunking
│   │   │   ├── embedder.py           # Vertex AI embeddings
│   │   │   └── chunker.py           # Basic chunker
│   │   ├── rag/
│   │   │   ├── rag_services.py       # Q&A, Docs, Completion, Editing
│   │   │   ├── vector_search.py      # Semantic similarity search
│   │   │   └── llm_client_gemini_api.py  # Gemini API client
│   │   ├── github/
│   │   │   └── github_client.py      # GitHub push/PR operations
│   │   └── utils/
│   │       ├── storage_utils.py      # Multi-tenant storage paths
│   │       ├── commit_tracker.py     # Commit tracking for caching
│   │       └── file_manager.py       # Local file management
│   ├── scripts/              # CLI tools for manual pipeline runs
│   ├── Dockerfile
│   └── requirements.txt
│
├── .env                      # Shared environment variables
├── setup-env.sh             # Mac/Linux setup script
├── setup-env.bat            # Windows setup script
├── README.md
└── requirements.txt         # Root-level dependencies
```

---

## Prerequisites

- **Python** 3.11+
- **Node.js** 18+ (for frontend)
- **Docker** (for containerized deployment)
- **GCP Account** with billing enabled
- **GitHub Account**
- **Gemini API Key** — free from [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/otto-pm/otto.git
cd otto
```

### 2. Configure Environment Variables

Create `otto/.env` (shared config):
```bash
# GCP
GCP_PROJECT_ID=otto-pm
GCS_BUCKET_RAW=otto-raw-repos
GCS_BUCKET_PROCESSED=otto-processed-chunks
GEMINI_API_KEY=your_gemini_api_key

# GitHub App
GITHUB_APP_ID=your_app_id
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_PRIVATE_KEY_PATH=./github-app-private-key.pem
GITHUB_CALLBACK_URL=http://localhost:8000/auth/github/callback

# Webhook
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Services
INGEST_SERVICE_URL=http://localhost:8081
FRONTEND_URL=http://localhost:3000
```

Create `backend/.env.local` (backend-specific):
```bash
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_PROJECT_ID=otto-pm
JWT_SECRET_KEY=generate_with_python_secrets_token_urlsafe_32
```

### 3. GCP Setup
```bash
# Authenticate
gcloud auth login
gcloud config set project otto-pm

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com

# Create storage buckets
gsutil mb -p otto-pm -l us-central1 gs://otto-raw-repos
gsutil mb -p otto-pm -l us-central1 gs://otto-processed-chunks
```
## Data Version Control (DVC)

We use DVC to track large data files and models. Data is stored in Google Cloud Storage.

### First-time setup

```bash
pip install dvc dvc-gs
gcloud auth application-default login
```

### Pull existing data

```bash
dvc pull
```

### Track new or updated data

**Important:** Always run `dvc add` before `git add` to avoid committing large files.

```bash
dvc add data/raw/your-file.csv       # 1. DVC tracks data, creates .dvc file
git add data/raw/your-file.csv.dvc   # 2. Git tracks the .dvc pointer
git commit -m "Add/update dataset"
dvc push                              # Upload data to GCS
git push                              # Push .dvc file to GitHub
```

---

### 4. GitHub App Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/apps) → New GitHub App
2. Set **Homepage URL**: `http://localhost:8000`
3. Set **Callback URL**: `http://localhost:8000/auth/github/callback`
4. Set **Webhook URL**: Your smee.io URL (for development)
5. Set **Webhook Secret**: Same as `GITHUB_WEBHOOK_SECRET` in `.env`
6. Enable permissions: Repository contents (read), Pull requests (write), Webhooks
7. Subscribe to events: Push
8. Download the private key and save as `backend/github-app-private-key.pem`

### 5. Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
2. Enable Firestore
3. Generate a service account key
4. Save as `backend/firebase-credentials.json`

---

## Running Locally

### Backend (port 8000)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Ingest Service (port 8081)
```bash
cd ingest-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8081
```

### Frontend (port 3000)
```bash
cd frontend
npm install
npm run dev
```

### Webhook Development (smee.io)
```bash
npx smee-client -u https://smee.io/YOUR_CHANNEL --target http://localhost:8000/webhook/github
```

---

## Deployment (GCP Cloud Run)

### Deploy Ingest Service
```bash
cd ingest-service
gcloud run deploy ingest-service \
  --source . \
  --region us-east1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300 \
  --set-env-vars "\
GCP_PROJECT_ID=otto-pm,\
GCS_BUCKET_RAW=otto-raw-repos,\
GCS_BUCKET_PROCESSED=otto-processed-chunks,\
GEMINI_API_KEY=your_key"
```

### Deploy Backend
```bash
cd backend
gcloud run deploy backend-service \
  --source . \
  --region us-east1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars "\
GCP_PROJECT_ID=otto-pm,\
GCS_BUCKET_RAW=otto-raw-repos,\
GCS_BUCKET_PROCESSED=otto-processed-chunks,\
INGEST_SERVICE_URL=https://ingest-service-xxxxx.us-east1.run.app,\
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json,\
FIREBASE_PROJECT_ID=otto-pm,\
GITHUB_PRIVATE_KEY_PATH=./github-app-private-key.pem,\
GITHUB_APP_ID=your_app_id,\
GITHUB_CLIENT_ID=your_client_id,\
GITHUB_CLIENT_SECRET=your_secret,\
GITHUB_CALLBACK_URL=https://backend-service-xxxxx.us-east1.run.app/auth/github/callback,\
JWT_SECRET_KEY=your_jwt_secret,\
GITHUB_WEBHOOK_SECRET=your_webhook_secret"
```

### Post-Deployment

1. Update GitHub App callback URL to your Cloud Run backend URL
2. Update GitHub App webhook URL to `https://your-backend-url/webhook/github`
3. Grant Cloud Run service account access to GCS buckets:
```bash
SERVICE_ACCOUNT=YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com

gsutil iam ch serviceAccount:$SERVICE_ACCOUNT:roles/storage.objectAdmin gs://otto-raw-repos
gsutil iam ch serviceAccount:$SERVICE_ACCOUNT:roles/storage.objectAdmin gs://otto-processed-chunks

gcloud projects add-iam-policy-binding otto-pm \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"
```

### Deployed Services

| Service | URL |
|---------|-----|
| Backend | `https://backend-service-484671782718.us-east1.run.app` |
| Ingest | `https://ingest-service-484671782718.us-east1.run.app` |

---

## API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | GET | Initiate GitHub OAuth flow |
| `/auth/github/callback` | GET | OAuth callback handler |
| `/auth/logout` | POST | Clear session |

### Pipeline

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/repos/pipeline` | POST | Run full pipeline (ingest → chunk → embed) |
| `/rag/repos/ingest` | POST | Ingest repository from GitHub |
| `/rag/repos/process` | POST | Chunk repository code |
| `/rag/repos/embed` | POST | Generate embeddings |

### RAG Services

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/ask` | POST | Ask a question about the codebase |
| `/rag/docs/generate` | POST | Generate documentation |
| `/rag/code/complete` | POST | Get code completion |
| `/rag/code/edit` | POST | Edit code with instructions |
| `/rag/search` | POST | Search code semantically |

### Streaming

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/ask/stream` | POST | Q&A with streaming response |
| `/rag/docs/generate/stream` | POST | Documentation with streaming |
| `/rag/code/edit/stream` | POST | Code editing with streaming |

### Repository Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/repos/user/history` | GET | User's repo access history |
| `/rag/repos/user/all` | GET | List all user's GitHub repos |
| `/rag/repos/{owner}/{repo}/status` | GET | Pipeline status for a repo |
| `/rag/repos/{owner}/{repo}/commit-history` | GET | Processing history |
| `/rag/repos/{owner}/{repo}/access` | GET | Check user's repo access |
| `/rag/repos/indexed` | GET | List all indexed repos |

### Webhooks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook/github` | POST | GitHub webhook receiver |
| `/webhook/active-sessions` | GET | View active webhook sessions |

### User Preferences

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/repos/user/preferences` | POST | Save repo preferences |
| `/rag/repos/{owner}/{repo}/preferences` | GET | Get repo preferences |

### Health & Stats

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/health` | GET | Backend + ingest service health |
| `/rag/stats` | GET | System statistics |

---

## RAG Pipeline Details

### 1. Ingestion

The ingester connects to GitHub's API, fetches the repository tree, filters for code files, and uploads them to Cloud Storage.

**Supported languages:** Python, JavaScript, TypeScript, Java, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, SQL, HTML, CSS, YAML, JSON, Markdown

**Excluded paths:** `node_modules`, `venv`, `__pycache__`, `.git`, `dist`, `build`, `coverage`

### 2. Chunking

The enhanced chunker uses tree-sitter for semantic parsing and extracts rich context for each chunk including type hints, docstrings, decorators, imports, and exception handling.

**Default settings:** 150 lines per chunk, 10 lines overlap

### 3. Embedding

Embeddings are generated using Vertex AI's `text-embedding-004` model in batches of 25, producing 768-dimensional vectors stored alongside the chunks.

### 4. Vector Search

Queries are embedded and compared against chunk embeddings using cosine similarity to find the most relevant code sections, which are then passed to Gemini for response generation.

---

## Webhook Flow
```
Developer pushes to main
        │
        ▼
GitHub sends push event → Backend /webhook/github
        │
        ├── Verify HMAC signature
        ├── Check: Is repo indexed?
        ├── Check: Is repo owner logged in?
        ├── Check: Is push to tracked branch?
        │
        ▼
Queue background pipeline
        │
        ├── Ingest (fetch new files)
        ├── Chunk (re-process code)
        └── Embed (regenerate vectors)
        │
        ▼
RAG is now up-to-date with latest code
```

If the user was logged out during the push, the sync happens automatically on next login.

---

## Cost Estimate

### Development (Free Tier)

| Service | Cost |
|---------|------|
| Gemini API | Free (15 req/min, 1M tokens/day) |
| Cloud Storage | ~$0.50/month |
| Vertex AI Embeddings | ~$0.025 per 1K embeddings |
| Cloud Run | Free tier covers light usage |
| **Total** | **~$5-10/month** |

### Production

| Service | Cost |
|---------|------|
| Cloud Run (2 services) | ~$10-20/month (scales to zero) |
| Cloud Storage | ~$1-5/month |
| Vertex AI | ~$5-15/month |
| **Total** | **~$20-40/month** |

---

## Troubleshooting

### Authentication Errors
```bash
gcloud auth application-default login
gcloud auth list
```

### Bucket Permission Denied
```bash
# Grant access to Cloud Run service account
gsutil iam ch serviceAccount:YOUR_SA:roles/storage.objectAdmin gs://BUCKET_NAME
```

### Webhook Not Triggering

1. Check smee.io page for incoming events
2. Verify webhook secret matches in GitHub App and `.env`
3. Ensure the push is to the tracked branch (usually `main`)
4. Confirm user is logged in (check `/webhook/active-sessions`)

### Ingest Service Unreachable
```bash
# Check health
curl https://ingest-service-xxxxx.us-east1.run.app/health

# Check logs
gcloud run services logs read ingest-service --region=us-east1
```

### Cloud Run Build Failures
```bash
# Check build logs
gcloud builds list --region=us-east1
gcloud builds log BUILD_ID --region=us-east1
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Built with care for the Otto Project — Northeastern University**
