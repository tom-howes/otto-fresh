<<<<<<< HEAD
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

## Cloud Setup

1. Clone the repo: `git clone https://github.com/otto-pm/otto.git`
2. Authenticate with GCP: `gcloud auth login`
3. Set the project: `gcloud config set project otto-pm`
4. Run the setup script:
   - **Windows:** `setup-env.bat`
   - **Mac/Linux:** `chmod +x setup-env.sh && ./setup-env.sh`
=======
>>>>>>> 155f254 (Squashed 'ingest-service/' content from commit 2198208)
Otto - AI-Powered Code RAG System
=================================

**Comprehensive data pipeline for GitHub repository ingestion, intelligent chunking, and RAG-based code assistance.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/) [![GCP](https://img.shields.io/badge/cloud-GCP-4285F4.svg)](https://cloud.google.com/) [![License](https://img.shields.io/badge/license-MIT-green.svg)](https://claude.ai/chat/LICENSE)

* * * * *

📋 Table of Contents
--------------------

-   [Overview](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#overview)
-   [Features](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#features)
-   [Architecture](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#architecture)
-   [Prerequisites](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#prerequisites)
-   [Installation](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#installation)
-   [Configuration](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#configuration)
-   [Usage](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#usage)
    -   [1\. Repository Ingestion](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#1-repository-ingestion)
    -   [2\. Code Chunking](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#2-code-chunking)
    -   [3\. Embedding Generation](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#3-embedding-generation)
    -   [4\. RAG Services](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#4-rag-services)
-   [Project Structure](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#project-structure)
-   [API Reference](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#api-reference)
-   [Troubleshooting](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#troubleshooting)
-   [Contributing](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#contributing)
-   [License](https://claude.ai/chat/6cca505e-43f0-4430-9c40-6c2e977214f0#license)

* * * * *

🎯 Overview
-----------

Otto is an intelligent code analysis system that:

1.  **Ingests** GitHub repositories into Google Cloud Storage
2.  **Chunks** code semantically with rich context extraction
3.  **Embeds** chunks using Vertex AI for semantic search
4.  **Provides** RAG-based services: Q&A, Documentation, Code Completion, and Code Editing

Built for the **Otto Project** - a software engineering project management solution leveraging LLMs and RAG.

* * * * *

✨ Features
----------

### 🔄 Repository Ingestion

-   ✅ GitHub API integration with OAuth support
-   ✅ Automatic file filtering (code files only)
-   ✅ Metadata extraction and storage
-   ✅ Support for multiple programming languages

### 🧩 Intelligent Chunking

-   ✅ **Semantic chunking** using tree-sitter for Python, JavaScript, TypeScript, Java, Go
-   ✅ **Context enrichment**: type hints, docstrings, decorators, imports, exceptions
-   ✅ **Large chunks** (150 lines) for better LLM understanding
-   ✅ **Overlap** between chunks for continuity

### 🎯 Vector Embeddings

-   ✅ Vertex AI text-embedding-004 model
-   ✅ Batch processing (25 chunks at once)
-   ✅ Efficient retry and error handling
-   ✅ 100% embedding coverage

### 🤖 RAG Services

-   ✅ **Q&A**: Answer questions about codebase
-   ✅ **Documentation**: Generate API docs, user guides, technical docs, READMEs
-   ✅ **Code Completion**: Intelligent suggestions based on patterns
-   ✅ **Code Editing**: Modify code with instructions
-   ✅ **Streaming support** for real-time responses

* * * * *

🏗️ Architecture
----------------

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Repository                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              1. INGESTION (GitHub → GCS)                 │
│  - Fetch repo via GitHub API                             │
│  - Filter code files                                     │
│  - Store in otto-raw-repos bucket                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│           2. CHUNKING (Enhanced Context)                 │
│  - Semantic chunking (tree-sitter)                       │
│  - Extract: types, docstrings, decorators, imports      │
│  - Build enriched context for LLMs                       │
│  - Store in otto-processed-chunks bucket                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│        3. EMBEDDING (Vertex AI text-embedding-004)       │
│  - Batch generation (25 at a time)                       │
│  - 768-dimensional vectors                               │
│  - Update chunks with embeddings                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              4. RAG SERVICES (Gemini)                    │
│  - Vector search (semantic similarity)                   │
│  - Context retrieval (top-k chunks)                      │
│  - LLM generation (Gemini 1.5 Flash)                     │
│  - Q&A | Docs | Completion | Editing                     │
└─────────────────────────────────────────────────────────┘

```

* * * * *

📋 Prerequisites
----------------

### Required

-   **Python**: 3.11 or higher
-   **GCP Account**: With billing enabled
-   **GitHub Account**: For repository access
-   **Gemini API Key**: Free from [Google AI Studio](https://aistudio.google.com/app/apikey)

### GCP Services Required

-   Cloud Storage
-   Vertex AI (for embeddings)
-   IAM & Admin

* * * * *

🚀 Installation
---------------

### 1\. Clone the Repository

```
git clone https://github.com/Malav2002/ingest_repo.git
cd ingest_repo

```

### 2\. Set Up Python Environment

```
# Deactivate conda if active
conda deactivate

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

```

### 3\. Install Dependencies

```
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Install Gemini API SDK
pip install google-generativeai

```

### 4\. Install Google Cloud SDK

```
# Mac
brew install google-cloud-sdk

# Or download from:
# https://cloud.google.com/sdk/docs/install

```

### 5\. Authenticate with Google Cloud

```
# Login to GCP
gcloud auth login

# Set up application default credentials
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID

```

* * * * *

⚙️ Configuration
----------------

### 1\. GCP Setup

```
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Enable required APIs
gcloud services enable\
  cloudfunctions.googleapis.com\
  storage.googleapis.com\
  aiplatform.googleapis.com\
  compute.googleapis.com

# Create storage buckets
gsutil mb -p $PROJECT_ID -l us-central1 gs://otto-raw-repos
gsutil mb -p $PROJECT_ID -l us-central1 gs://otto-processed-chunks
gsutil mb -p $PROJECT_ID -l us-central1 gs://otto-dataflow-temp

```

### 2\. Get API Keys

#### GitHub Token

1.  Go to: https://github.com/settings/tokens
2.  Generate new token (classic)
3.  Select scope: `repo` (full control)
4.  Copy the token

#### Gemini API Key

1.  Go to: https://aistudio.google.com/app/apikey
2.  Click "Create API Key"
3.  Copy the key

### 3\. Configure Environment Variables

Create a `.env` file in the project root:

```
# .env file
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
BUCKET_RAW=otto-raw-repos
BUCKET_PROCESSED=otto-processed-chunks
BUCKET_TEMP=otto-dataflow-temp
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here

```

### 4\. Create `.gitignore`

```
# .gitignore
credentials.json
*.json
.env
venv/
__pycache__/
*.pyc
.DS_Store
*.log

```

* * * * *

📚 Usage
--------

### 1\. Repository Ingestion

Ingest a GitHub repository into Cloud Storage:

```
# Ingest a public repository
python scripts/ingest_repo.py owner/repository-name

# Example
python scripts/ingest_repo.py malav2002/ai-portfolio-analyzer

# Ingest a specific branch
python scripts/ingest_repo.py owner/repo --branch develop

# View help
python scripts/ingest_repo.py --help

```

**Output:**

-   Raw files stored in: `gs://otto-raw-repos/owner/repo/`
-   Metadata: `gs://otto-raw-repos/owner/repo/metadata.json`

* * * * *

### 2\. Code Chunking

Process ingested repository into intelligent chunks:

```
# Basic chunking (enhanced with context)
python scripts/process_repo.py owner/repository-name

# Example
python scripts/process_repo.py malav2002/ai-portfolio-analyzer

# Custom chunk size
python scripts/process_repo.py owner/repo --chunk-size 200 --overlap 15

# Use basic chunker (faster, less context)
python scripts/process_repo.py owner/repo --basic

# View help
python scripts/process_repo.py --help

```

**What happens:**

-   ✅ Semantic chunking with tree-sitter
-   ✅ Context extraction (types, docstrings, imports, decorators)
-   ✅ Enriched content for LLM understanding
-   ✅ Chunks saved to: `gs://otto-processed-chunks/owner/repo/chunks.jsonl`

**Typical output:**

```
🔧 Processing repository: malav2002/ai-portfolio-analyzer
📁 Processing 35 files with larger chunk size (150 lines)
✓ 35/35 files (285 chunks, 7.0 files/sec)
⚡ Chunking completed in 5.0s
✅ Created 285 context-rich chunks

```

* * * * *

### 3\. Embedding Generation

Generate embeddings for semantic search:

```
# Generate embeddings for all chunks
python scripts/embed_repo.py owner/repository-name

# Example
python scripts/embed_repo.py malav2002/ai-portfolio-analyzer

# Force re-embed existing embeddings
python scripts/embed_repo.py owner/repo --force

# Custom batch size
python scripts/embed_repo.py owner/repo --batch-size 50

# View help
python scripts/embed_repo.py --help

```

**What happens:**

-   ✅ Loads chunks from GCS
-   ✅ Generates embeddings using Vertex AI (text-embedding-004)
-   ✅ Batch processing for efficiency
-   ✅ Updates chunks with 768-dimensional vectors

**Typical output:**

```
📦 Loaded: 285 chunks
🎯 Chunks to embed: 285
🔄 Generating embeddings (batch size: 25)...
  ✓ 285/285 embeddings (12.5/sec)
✅ Generated 285 embeddings in 22.8s

```

* * * * *

### 4\. RAG Services

Use the RAG system for code assistance:

#### 4.1. Q&A Service

Answer questions about your codebase:

```
# Ask a question
python scripts/rag_cli.py owner/repo\
  --service qa\
  --question "How does the OCR service handle errors?"

# With streaming (see response in real-time)
python scripts/rag_cli.py owner/repo\
  --service qa\
  --question "What caching mechanism is used?"\
  --stream

# Filter by language
python scripts/rag_cli.py owner/repo\
  --service qa\
  --question "How is authentication implemented?"\
  --language python

```

**Example:**

```
python scripts/rag_cli.py malav2002/ai-portfolio-analyzer\
  --service qa\
  --question "How does the OCR service handle errors?"\
  --stream

```

#### 4.2. Documentation Generation

Generate professional documentation:

```
# Generate API documentation
python scripts/rag_cli.py owner/repo\
  --service doc\
  --target "portfolio analysis API"\
  --doc-type api\
  --stream

# Generate user guide
python scripts/rag_cli.py owner/repo\
  --service doc\
  --target "getting started"\
  --doc-type user_guide\
  --stream

# Generate technical documentation
python scripts/rag_cli.py owner/repo\
  --service doc\
  --target "OCR service architecture"\
  --doc-type technical\
  --stream

# Generate README
python scripts/rag_cli.py owner/repo\
  --service doc\
  --target "project overview"\
  --doc-type readme\
  --stream

```

**Documentation types:**

-   `api` - API reference with function signatures
-   `user_guide` - Step-by-step user instructions
-   `technical` - Technical architecture and implementation
-   `readme` - Complete README.md

#### 4.3. Code Completion

Get intelligent code suggestions:

```
# Complete code
python scripts/rag_cli.py owner/repo\
  --service complete\
  --code "async def process_portfolio(image_path: str):"\
  --language python\
  --stream

# Example
python scripts/rag_cli.py malav2002/ai-portfolio-analyzer\
  --service complete\
  --code "def extract_text(image):"\
  --language python

```

#### 4.4. Code Editing

Modify existing code based on instructions:

```
# Edit code with instructions
python scripts/rag_cli.py owner/repo\
  --service edit\
  --file "services/ocr_service.py"\
  --instruction "add retry logic and better error handling"\
  --stream

# Example
python scripts/rag_cli.py malav2002/ai-portfolio-analyzer\
  --service edit\
  --file "ml-service/src/services/ocr_service.py"\
  --instruction "add rate limiting"\
  --stream

```

* * * * *

📁 Project Structure
--------------------

```
ingest_repo/
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── github_ingester.py        # GitHub API integration
│   ├── chunking/
│   │   ├── __init__.py
│   │   ├── chunker.py                # Basic chunker
│   │   ├── enhanced_chunker.py       # Enhanced context extraction
│   │   └── embedder.py               # Embedding generation
│   └── rag/
│       ├── __init__.py
│       ├── llm_client_gemini_api.py  # Gemini API client
│       ├── vector_search.py          # Semantic search
│       └── rag_services.py           # Q&A, Docs, Completion, Editing
├── scripts/
│   ├── ingest_repo.py                # CLI: Ingest repository
│   ├── process_repo.py               # CLI: Chunk repository
│   ├── embed_repo.py                 # CLI: Generate embeddings
│   ├── rag_cli.py                    # CLI: RAG services
│   ├── inspect_chunks.py             # Analyze chunk quality
│   └── analyze_chunk_quality.py      # Quality metrics
├── tests/
│   ├── test_ingestion.py
│   └── test_chunking.py
├── requirements.txt                   # Python dependencies
├── .env                              # Environment variables (don't commit!)
├── .gitignore
└── README.md

```

* * * * *

🔧 API Reference
----------------

### Ingestion

```
from src.ingestion.github_ingester import GitHubIngester

ingester = GitHubIngester(
    project_id="your-project-id",
    bucket_name="otto-raw-repos",
    github_token="your_token"
)

metadata = ingester.ingest_repository("owner/repo", branch="main")

```

### Chunking

```
from src.chunking.enhanced_chunker import EnhancedCodeChunker

chunker = EnhancedCodeChunker(
    project_id="your-project-id",
    bucket_raw="otto-raw-repos",
    bucket_processed="otto-processed-chunks"
)

chunks = chunker.process_repository("owner/repo")

```

### Embeddings

```
from src.chunking.embedder import ChunkEmbedder

embedder = ChunkEmbedder(
    project_id="your-project-id",
    bucket_processed="otto-processed-chunks"
)

stats = embedder.embed_repository("owner/repo")

```

### RAG Services

```
from src.rag.rag_services import RAGServices

rag = RAGServices(
    project_id="your-project-id",
    bucket_processed="otto-processed-chunks"
)

# Q&A
result = rag.answer_question("How does X work?", "owner/repo")

# Documentation
docs = rag.generate_documentation("API", "owner/repo", doc_type="api")

# Code completion
completion = rag.complete_code("def process_", "", "owner/repo", "python")

# Code editing
edited = rag.edit_code("add error handling", "file.py", "owner/repo")

```

* * * * *

🐛 Troubleshooting
------------------

### Common Issues

#### 1\. **Authentication Errors**

```
# Re-authenticate
gcloud auth application-default login

# Check credentials
gcloud auth list

```

#### 2\. **Bucket Not Found**

```
# List buckets
gsutil ls

# Create missing buckets
gsutil mb gs://otto-raw-repos
gsutil mb gs://otto-processed-chunks

```

#### 3\. **API Not Enabled**

```
# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com

```

#### 4\. **Gemini API Key Issues**

```
# Verify key is set
echo $GEMINI_API_KEY

# Get new key from: https://aistudio.google.com/app/apikey

```

#### 5\. **Embedding Timeouts**

```
# Check network connectivity
ping us-central1-aiplatform.googleapis.com

# Try different region
python scripts/embed_repo.py owner/repo --location us-east4

```

#### 6\. **Module Not Found**

```
# Reinstall dependencies
pip install -r requirements.txt
pip install google-generativeai

```

* * * * *

📊 Performance Metrics
----------------------

Based on testing with **malav2002/ai-portfolio-analyzer** (35 files):

| Metric | Value |
| --- | --- |
| **Ingestion Speed** | ~6 files/sec |
| **Chunking Speed** | ~7 files/sec |
| **Total Chunks** | 285 |
| **Avg Chunk Size** | 2,784 chars |
| **Embedding Speed** | ~12/sec |
| **Semantic Coverage** | 95.4% |
| **Import Context** | 68.4% |

**Quality Scores:**

-   ✅ **Documentation Generation**: Excellent (high semantic chunks)
-   ✅ **Code Completion**: Good (70% focused chunks)
-   ✅ **Q&A Search**: Excellent (100% embeddings)

* * * * *

💰 Cost Estimate
----------------

### Free Tier (Recommended)

-   **Gemini API**: FREE (15 req/min, 1M tokens/day)
-   **Cloud Storage**: $0.02/GB/month (~$0.50/month for typical use)
-   **Vertex AI Embeddings**: ~$0.025 per 1K embeddings (~$7 for 285 chunks)

**Total**: ~$8/month for moderate use

### Production Tier

-   **Gemini 1.5 Pro**: $1.25 per 1M input tokens
-   Scalable based on usage

* * * * *

🤝 Contributing
---------------

Contributions welcome! Please follow these steps:

1.  Fork the repository
2.  Create a feature branch: `git checkout -b feature/amazing-feature`
3.  Commit changes: `git commit -m 'Add amazing feature'`
4.  Push to branch: `git push origin feature/amazing-feature`
5.  Open a Pull Request

* * * * *

📝 License
----------

This project is part of the **Otto** software engineering project management system.

* * * * *

🙏 Acknowledgments
------------------

-   **Google Cloud Platform** for infrastructure
-   **Vertex AI** for embeddings
-   **Gemini** for LLM capabilities
-   **tree-sitter** for semantic parsing

* * * * *

📞 Support
----------

For issues and questions:

-   Open an issue on GitHub
-   Contact: me

* * * * *

🚀 Quick Start Summary
----------------------

```
# 1. Setup
git clone https://github.com/Malav2002/ingest_repo.git
cd ingest_repo
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install google-generativeai

# 2. Configure
# Add to .env: PROJECT_ID, GEMINI_API_KEY, GITHUB_TOKEN

# 3. Create GCP resources
gcloud services enable aiplatform.googleapis.com storage.googleapis.com
gsutil mb gs://otto-raw-repos
gsutil mb gs://otto-processed-chunks

# 4. Use the pipeline
python scripts/ingest_repo.py owner/repo
python scripts/process_repo.py owner/repo
python scripts/embed_repo.py owner/repo

# 5. Ask questions!
python scripts/rag_cli.py owner/repo\
  --service qa\
  --question "How does this work?"\
  --stream

```

* * * * *

**Built with ❤️ for the Otto Project**
# webhook test
