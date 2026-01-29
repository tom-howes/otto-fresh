# OTTO

AI-powered project management tool with repository-aware Q&A and automated task generation.

## Features

- **Q&A Agent**: Ask questions about your codebase and get contextual answers via RAG
- **Task Generation**: Input product requirements, receive structured Kanban tasks as JSON
- **GitHub Integration**: Connect repositories, auto-sync on push to main

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| Frontend | Next.js 14, React, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Database | Firestore, Cloud Storage |
| ML/AI | Vertex AI (Gemini 1.5 Pro, fine-tuned with LoRA), Vector Search (ScaNN), Embeddings API |
| Infrastructure | GCP, Cloud Run, Terraform, Cloud Build |

## Prerequisites

- Node.js 18+
- Python 3.11+
- Docker
- GCP account with billing enabled
- GitHub account

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/otto-pm/otto
cd otto

# Frontend
cd frontend && npm install

# Backend
cd ../backend && pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment templates
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env

# Required variables:
# - GOOGLE_CLOUD_PROJECT
# - FIREBASE_API_KEY
# - GITHUB_APP_ID
# - GITHUB_PRIVATE_KEY
```

### 3. Deploy Infrastructure

```bash
cd infrastructure/terraform
terraform init
terraform apply -var-file=environments/staging.tfvars
```

### 4. Run Locally

```bash
# Terminal 1 - Backend
cd backend && uvicorn src.main:app --reload

# Terminal 2 - Frontend
cd frontend && npm run dev
```

App available at `http://localhost:3000`

## Usage

### Connect a Repository
1. Sign in with GitHub
2. Click "Connect Repository"
3. Select repository and authorize access
4. Wait for initial indexing to complete

### Q&A Mode
```
[QANDA] How does the authentication middleware work?
```

### Task Generation Mode
```
[TASKGEN] Build user login with OAuth support
```

Returns structured JSON with tasks, acceptance criteria, and estimates.

## Project Structure

```
otto/
├── frontend/          # Next.js app
├── backend/           # FastAPI services
├── ml/                # Pipelines, fine-tuning, evaluation
├── infrastructure/    # Terraform, Cloud Build configs
├── tests/             # Unit and integration tests
└── docs/              # Documentation
```

## Development

```bash
# Run tests
cd backend && pytest
cd frontend && npm test

# Build Docker images
docker build -t otto-backend ./backend
docker build -t otto-ml ./ml
```
