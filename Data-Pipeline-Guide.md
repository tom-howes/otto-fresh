# Otto — Data Pipeline Testing Guide

**Project:** Otto — AI-Powered Code Repository Management System
**Team:** Malav Patel, Siddharth Trivedi
**Course:** MLOps
**Date:** February 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [How to Generate a GitHub Personal Access Token](#2-how-to-generate-a-github-personal-access-token)
3. [Testing the Deployed Pipeline](#3-testing-the-deployed-pipeline)
   - 3.1 Health Check
   - 3.2 Full Pipeline Run (Ingest + Chunk + Embed)
   - 3.3 Ingest Stage
   - 3.4 Chunk Stage
   - 3.5 Embed Stage
   - 3.6 Force Re-Embedding
   - 3.7 Pipeline Status Check
   - 3.8 Ask a Question (RAG Q&A)
   - 3.9 Semantic Code Search
   - 3.10 Documentation Generation
   - 3.11 Code Completion
   - 3.12 Code Editing
4. [Testing the DVC Pipeline](#4-testing-the-dvc-pipeline)
   - 4.1 Clone and Setup
   - 4.2 Initialize DVC
   - 4.3 View the Pipeline DAG
   - 4.4 Run the Full Pipeline
   - 4.5 Run Individual Stages
   - 4.6 Inspect Stage Outputs
   - 4.7 Verify DVC Tracking
5. [Running the Test Suite (69 Tests)](#5-running-the-test-suite-69-tests)
6. [Data Validation & Monitoring](#6-data-validation--monitoring)
7. [Pipeline Architecture Reference](#7-pipeline-architecture-reference)
8. [Troubleshooting](#8-troubleshooting)
9. [Quick Reference — Complete Test Sequence](#9-quick-reference--complete-test-sequence)

---

## 1. Overview

Otto's data pipeline ingests source code from GitHub repositories, chunks the code using Tree-sitter AST parsing, generates vector embeddings via Vertex AI, and stores everything in Google Cloud Storage. Post-embedding, it runs schema validation, anomaly detection, and bias detection.

**Pipeline Stages:**

```
Ingest → Chunk → Embed → Schema Validation → Anomaly Detection → Bias Detection
```

The pipeline is **fully deployed on Google Cloud Run** — no local environment setup is required to test the core pipeline. You can test every endpoint using `curl` from your terminal with **any GitHub repository you have access to** (public or private).

A separate section (Section 4) covers running the DVC pipeline locally if you'd like to verify the DVC configuration and reproducibility.

---

## 2. How to Generate a GitHub Personal Access Token

You will need a GitHub **Personal Access Token (PAT)** with `repo` scope to allow the pipeline to read repository contents. You can use **any repository you own or have access to** for testing.

### Step-by-Step

1. **Go to GitHub Settings**
   - Log in to [https://github.com](https://github.com)
   - Click your **profile picture** (top-right) → **Settings**

2. **Navigate to Developer Settings**
   - Scroll to the very bottom of the left sidebar → click **Developer settings**

3. **Create a New Token**
   - Click **Personal access tokens** → **Tokens (classic)**
   - Click **Generate new token** → **Generate new token (classic)**
   - GitHub may ask you to confirm your password or 2FA

4. **Configure the Token**
   - **Note:** `Otto Pipeline Testing`
   - **Expiration:** `30 days` (or shorter if preferred)
   - **Scopes:** Check the following:
     - ✅ **`repo`** — Full control of private repositories
       - This automatically includes `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
   - If you only plan to test with **public repositories**, checking just `public_repo` is sufficient

5. **Generate and Copy**
   - Click **Generate token**
   - **⚠️ Copy the token immediately** — GitHub will never show it again
   - The token looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

6. **Save for Use**
   - Store the token securely — you'll use it in the `curl` commands below
   - Never commit tokens to version control

### Quick Verification

Confirm your token works by running:

```bash
curl -H "Authorization: token YOUR_GITHUB_TOKEN" https://api.github.com/user
```

You should see your GitHub profile information in the response.

---

## 3. Testing the Deployed Pipeline

The pipeline services are live on Google Cloud Run. All you need is **a terminal with `curl`** and your GitHub token from Step 2.

**Base URL:**
```
https://ingest-service-484671782718.us-east1.run.app
```

**Replace these placeholders in every command below:**
- `YOUR_GITHUB_TOKEN` → your PAT from Step 2
- `owner/repo` → any repository you have access to (e.g., `your-username/your-repo`)

---

### 3.1 Health Check

Verify the service is running (no token needed):

```bash
curl https://ingest-service-484671782718.us-east1.run.app/health
```

**Expected Response:**
```json
{"status": "healthy"}
```

---

### 3.2 Full Pipeline Run (Ingest + Chunk + Embed)

This is the **primary test** — it downloads the repository, chunks all source code using Tree-sitter, and generates 768-dimensional vector embeddings via Vertex AI:

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "github_token": "YOUR_GITHUB_TOKEN",
    "force_reembed": false
  }'
```

**What happens behind the scenes:**
1. **Ingest** — Clones repo contents via GitHub API, stores raw files in GCS (`otto-pm-raw-repos`)
2. **Chunk** — Parses each file with Tree-sitter (150 lines per chunk, 10 line overlap)
3. **Embed** — Sends chunks to Vertex AI `text-embedding-004` in batches of 250, stores `chunks.jsonl` in GCS (`otto-pm-processed-chunks`)
4. **Validate** — Runs schema validation, anomaly detection, and bias detection automatically

**Expected Response:** JSON with status for each stage, file counts, chunk counts, and embedding counts.

> **Note:** First run on a repo may take 1–3 minutes depending on repo size. Subsequent runs are incremental (only changed files are reprocessed).

---

### 3.3 Ingest Stage (Download Repo Files)

Run just the ingestion — downloads repo files from GitHub to Google Cloud Storage:

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "github_token": "YOUR_GITHUB_TOKEN"
  }'
```

**What it does:** Fetches all source files via the GitHub API and stores them in `gs://otto-pm-raw-repos/repos/{owner}/{repo}/`.

---

### 3.4 Chunk Stage (Parse Code into Chunks)

Run just the chunking — requires ingestion to have been completed first:

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo"
  }'
```

**What it does:** Uses Tree-sitter AST parsing to split source files into semantically meaningful chunks (150 lines each, 10 line overlap). Supports Python, JavaScript, TypeScript, Java, Go, Rust, C, C++, and more.

---

### 3.5 Embed Stage (Generate Vector Embeddings)

Run just the embedding — requires chunking to have been completed first:

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/embed \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "force_reembed": false
  }'
```

**What it does:** Generates 768-dimensional embeddings for each chunk using Vertex AI `text-embedding-004` (batch size 250). Stores results in `gs://otto-pm-processed-chunks/repos/{owner}/{repo}/chunks.jsonl`.

---

### 3.6 Force Re-Embedding

To clear all existing embeddings and regenerate from scratch (useful after major code changes):

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/embed \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "force_reembed": true
  }'
```

---

### 3.7 Pipeline Status Check

Check the current pipeline status for any repo:

```bash
curl https://ingest-service-484671782718.us-east1.run.app/pipeline/repos/owner/repo/status
```

**Expected Response:** JSON containing ingestion status, chunk count, embedding count, last processed commit, and timestamps.

---

### 3.8 Ask a Question (RAG Q&A)

After the pipeline has run on a repo, you can ask natural language questions about the codebase. Otto retrieves relevant code chunks via vector search and generates an answer using Gemini 1.5 Flash:

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/ask \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "question": "How does the main entry point work?",
    "github_token": "YOUR_GITHUB_TOKEN"
  }'
```

**Try different questions to test RAG quality:**
- `"What are the main classes in this project?"`
- `"How is error handling implemented?"`
- `"What dependencies does this project use?"`
- `"Explain the database or data storage logic."`

---

### 3.9 Semantic Code Search

Search the codebase using natural language. Returns the top-k most relevant code chunks ranked by cosine similarity:

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/search \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "query": "authentication and login",
    "top_k": 5
  }'
```

**Expected Response:** Array of code chunks with similarity scores, file paths, language, and line numbers. Results above the 0.6 similarity threshold are considered relevant.

---

### 3.10 Documentation Generation

Automatically generate documentation for a specific file in the repository:

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/docs/generate \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "target": "path/to/file.py",
    "doc_type": "api",
    "github_token": "YOUR_GITHUB_TOKEN",
    "push_to_github": false
  }'
```

**Parameters:**
- `target` — relative file path within the repo (e.g., `src/main.py`, `app/routes/auth.py`)
- `doc_type` — type of documentation (`"api"`, `"module"`, `"readme"`)
- `push_to_github` — set to `true` to create a branch and PR with the generated docs; `false` to just return the content

---

### 3.11 Code Completion

Get AI-powered code completion. You provide a code snippet and Otto automatically detects which file in the repo it belongs to using semantic similarity search (threshold > 0.6), then generates a contextually aware completion:

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/code/complete \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "code_context": "def calculate_total(items):\n    total = 0\n    for item in items:",
    "language": "python",
    "github_token": "YOUR_GITHUB_TOKEN"
  }'
```

**How it works:**
1. Otto takes your `code_context` snippet and searches the indexed repo for the most similar code
2. It auto-detects which file the snippet belongs to (returned as `detected_file` in the response)
3. It generates a completion that matches the repository's coding style and patterns
4. If `push_to_github` is set to `true`, Otto fetches the actual file from GitHub, surgically inserts the completion at the correct position, and creates a PR

**With GitHub push (auto-detects file, creates branch + PR):**

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/code/complete \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "code_context": "def calculate_total(items):\n    total = 0\n    for item in items:",
    "language": "python",
    "push_to_github": true,
    "github_token": "YOUR_GITHUB_TOKEN"
  }'
```

> **Tip:** The more specific your `code_context` is (unique function names, class signatures), the more accurately Otto detects the target file. Generic snippets may fall below the 0.6 similarity threshold.

---

### 3.12 Code Editing

Request AI-generated code edits using natural language instructions. Otto automatically detects the target file from your instruction using semantic search — you don't need to specify a file path (though you can optionally provide one):

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/code/edit \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "instruction": "Add input validation and error handling to the calculate_total function",
    "github_token": "YOUR_GITHUB_TOKEN"
  }'
```

**How it works:**
1. Otto takes your natural language `instruction` and searches the indexed repo to find the most relevant file
2. It auto-detects the target file (returned as `detected_file` in the response)
3. It fetches the actual current file content from GitHub
4. It makes **surgical edits** — only modifying what the instruction asks for while preserving everything else
5. Returns the complete modified file content

**With explicit target file (skips auto-detection):**

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/code/edit \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "instruction": "Add logging to all API endpoints",
    "target_file": "src/routes/api.py",
    "github_token": "YOUR_GITHUB_TOKEN"
  }'
```

**With GitHub push (creates branch + PR with the edit):**

```bash
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/code/edit \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "owner/repo",
    "instruction": "Add retry logic with exponential backoff to the API client",
    "push_to_github": true,
    "github_token": "YOUR_GITHUB_TOKEN"
  }'
```

> **Tip:** Include file names or specific function/class names in your instruction for more accurate auto-detection. For example, "Add error handling to the `UserService` class in auth.py" works better than "Add error handling".

---

## 4. Testing the DVC Pipeline

This section covers how to run and verify the DVC (Data Version Control) pipeline locally. This requires a local environment setup. 

### 4.1 Clone and Setup

```bash
# Clone the repository
git clone https://github.com/otto-pm/otto.git
cd otto/Data-Pipeline

# Create Python 3.11 virtual environment (required — 3.9/3.13 cause conflicts)
python3.11 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

> **Important:** Always use `python -m pytest` and `python -m dvc` to ensure the venv Python is used, not your system/Anaconda Python.

### 4.2 Authenticating the Google Cloud Security Account

1. A service account key will be provided with this submission named sa-key.json. Add this here: `otto/Data-Pipeline/sa-key.json`
2. Activate service account `gcloud auth activate-service-account --key-file=sa-key.json`
3. Set otto-pm as the project `gcloud config set project otto-pm`
4. Set the credentials for Python libraries:

   **macOS/Linux:**
```bash
   export GOOGLE_APPLICATION_CREDENTIALS="sa-key.json"
```

   **Windows (PowerShell):**
```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS="sa-key.json"
```

   **Windows (CMD):**
```cmd
   set GOOGLE_APPLICATION_CREDENTIALS=sa-key.json
```

### 4.3 Set Environment Variables

Replace `YOUR_GITHUB_TOKEN` with your personal access token.

**macOS/Linux:**
```bash
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
export GCP_PROJECT_ID="otto-pm"
export GCS_BUCKET_RAW="otto-pm-raw-repos"
export GCS_BUCKET_PROCESSED="otto-pm-processed-chunks"
export VERTEX_LOCATION="us-east1"
```

**Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
$env:GCP_PROJECT_ID="otto-pm"
$env:GCS_BUCKET_RAW="otto-pm-raw-repos"
$env:GCS_BUCKET_PROCESSED="otto-pm-processed-chunks"
$env:VERTEX_LOCATION="us-east1"
```

**Windows (CMD):**
```cmd
set GITHUB_TOKEN=YOUR_GITHUB_TOKEN
set GCP_PROJECT_ID=otto-pm
set GCS_BUCKET_RAW=otto-pm-raw-repos
set GCS_BUCKET_PROCESSED=otto-pm-processed-chunks
set VERTEX_LOCATION=us-east1
```

### 4.4 View the Pipeline DAG

Verify the pipeline structure:

```bash
dvc dag
```

**Expected Output:**

```
+--------+
| ingest |
+--------+
     *
     *
     *
 +-------+
 | chunk |
 +-------+
     *
     *
     *
 +-------+
 | embed |
 +-------+
     *
     *
     *
+----------+
| validate |
+----------+
```

The 4 stages and their dependencies are defined in `dvc.yaml`:

| Stage | Script | Description |
|-------|--------|-------------|
| **ingest** | `scripts/run_pipeline.py ingest` | Downloads repo files from GitHub to GCS |
| **chunk** | `scripts/run_pipeline.py chunk` | Parses code into chunks via Tree-sitter AST |
| **embed** | `scripts/run_pipeline.py embed` | Generates 768-dim embeddings via Vertex AI |
| **validate** | `scripts/schema_validation.py validate` | Validates chunk schema, performs anomaly and bias detection

### 4.5 Run the Full DVC Pipeline

```bash
dvc repro -f
```

This executes all 4 stages in dependency order. DVC tracks inputs and outputs and only reruns stages whose dependencies have changed. Anomaly, schema, and bias validation are all included in the validation step.

### 4.6 Run Individual DVC Stages

You can run any single stage (and its upstream dependencies if needed):

```bash
# Run only the ingest stage
dvc repro ingest

# Run only the chunk stage (will run ingest first if needed)
dvc repro chunk

# Run only the embed stage
dvc repro embed

# Run only the validation stage
dvc repro validate
```

### 4.7 Inspect Stage Outputs

After running the pipeline, verify the outputs:

```bash
# Check that raw data was downloaded
ls data/raw/

# Check that processed chunks exist
ls data/processed/

# Check validation reports and monitoring logs
cat logs/pipeline.log
cat data/processed/schema_validation.json
cat data/processed/bias_detection.json 
cat data/processed/anomaly_detection.json
```

### 4.8 Verify DVC Tracking

```bash
# Show current pipeline status (which stages are up-to-date)
dvc status

# Show the configured DVC remote (GCS)
dvc remote list

# View the full dvc.yaml configuration
cat dvc.yaml
```

---

## 5. Running the Test Suite (69 Tests)

The project includes **69 unit tests** across 3 modules covering data acquisition, preprocessing, and embedding. Tests use mocked fixtures — **no live API credentials are required**.

### Setup

```bash
cd otto/Data-Pipeline
python3.11 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Important:** Python 3.11 is required. Python 3.9 and 3.13 cause `google.cloud` namespace conflicts that prevent test collection.

### Run All Tests

```bash
python -m pytest tests/ -v
```

**Expected Output:** `69 passed`

### Run Tests by Module

```bash
# Data Acquisition — 20 tests
# Covers: GitHub URL parsing, language detection, file filtering,
# retry session creation, ingester initialization
python -m pytest tests/test_acquisition.py -v

# Data Preprocessing — 32 tests
# Covers: Python import/decorator/async/exception/global extraction,
# TypeScript interface/type/enum/generic extraction,
# JavaScript import/export extraction, Java annotation/interface extraction
python -m pytest tests/test_preprocessing.py -v

# Embedding — 17 tests
# Covers: Vertex AI model initialization, chunk loading/saving,
# batch embedding, force re-embed, text truncation, failure handling
python -m pytest tests/test_embedder.py -v
```

### Run with Coverage Report

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### Coverage Breakdown

| Module | Statements | Coverage | Notes |
|--------|-----------|----------|-------|
| `chunking/__init__.py` | 4 | **100%** | Package initialization |
| `chunking/embedder.py` | 126 | **87%** | Embedding generation, batch processing, caching |
| `chunking/enhanced_chunker.py` | 411 | **51%** | Python/TS/JS/Java metadata extraction methods |
| `ingestion/github_ingester.py` | 184 | **31%** | URL parsing, language detection, file filtering |
| `chunking/chunker.py` | 214 | **9%** | Core Tree-sitter parsing (heavy GCS I/O) |
| **TOTAL** | **939** | **43%** | |

**Why some modules have lower coverage:** The lower-coverage modules (`chunker.py` at 9%, `github_ingester.py` at 31%) contain heavy Google Cloud Storage and GitHub API I/O operations (file downloads, GCS uploads, API pagination). The tests mock around these external calls rather than exercising the I/O paths directly, which is the standard approach for unit tests — integration testing of live GCS/GitHub calls happens via the deployed Cloud Run pipeline (Section 3). The high-coverage modules (`embedder.py` at 87%, `enhanced_chunker.py` at 51%) are where the core data transformation and embedding logic lives, and these are thoroughly tested including edge cases like text truncation, batch failures, and force re-embedding.

### Test Configuration

Tests are configured in `tests/conftest.py` with shared pytest fixtures for mocking GitHub API responses, GCS operations, and Vertex AI embedding calls.

---

## 6. Data Validation & Monitoring

After embedding completes, three validation stages run automatically (both in the deployed pipeline and via DVC).

### 6.1 Schema Validation

Validates the structure of every generated chunk against 6 expectations:

1. Chunk content is non-empty
2. File paths are valid and well-formed
3. Language fields are populated
4. Embedding dimensions equal exactly 768
5. Line numbers are positive integers
6. Chunk IDs are unique (no duplicates)

**Log:** `Data-Pipeline/logs/schema_validation.log`

### 6.2 Anomaly Detection

Detects statistical outliers in chunk distributions:

- Unusually large or small chunks compared to the mean
- Embedding norm outliers (may indicate corrupted embeddings)
- Unexpected language distribution shifts
- Configured to send **Slack alerts** when anomalies exceed defined thresholds

**Log:** `Data-Pipeline/logs/anomaly_detection.log`

### 6.3 Bias Detection

Analyzes chunk distribution across 4 slicing strategies to ensure fair representation:

| Slice | What It Checks |
|-------|---------------|
| **By programming language** | No language is disproportionately over/under-represented |
| **By file size** | Coverage isn't biased toward large or small files |
| **By directory depth** | Nested directories get adequate representation |
| **By file extension** | Diverse file types are captured proportionally |

**Log:** `Data-Pipeline/logs/bias_detection.log`

---

## 7. Pipeline Architecture Reference

### Data Flow

```
GitHub Repository (any repo you have access to)
       │
       ▼
┌─────────────┐     Raw files stored in GCS
│   Ingest    │ ──► gs://otto-pm-raw-repos/repos/{owner}/{repo}/
└─────────────┘
       │
       ▼
┌─────────────┐     Tree-sitter AST parsing
│   Chunk     │     150 lines per chunk, 10 line overlap
└─────────────┘
       │
       ▼
┌─────────────┐     Vertex AI text-embedding-004
│   Embed     │     768 dimensions, batch size 250
└─────────────┘
       │
       ▼
  chunks.jsonl  ──► gs://otto-pm-processed-chunks/repos/{owner}/{repo}/
       │
       ▼
┌─────────────────────────────────────────────┐
│  Validate → Anomaly Detect → Bias Detect    │
└─────────────────────────────────────────────┘
```

### GCS Storage Layout

```
otto-pm-raw-repos/
└── repos/{owner}/{repo}/
    ├── metadata.json          # Repo metadata (stars, language, size, etc.)
    └── {all source files}     # Mirrored directory structure

otto-pm-processed-chunks/
└── repos/{owner}/{repo}/
    ├── chunks.jsonl           # Chunks with 768-dim embedding vectors
    ├── commit_info.json       # Latest processed commit metadata
    └── commit_history.jsonl   # Full commit history log
```

### Technology Stack

| Component | Technology | Details |
|-----------|-----------|---------|
| Deployment | Google Cloud Run | `us-east1` region |
| Embedding Model | Vertex AI `text-embedding-004` | 768 dimensions |
| LLM | Gemini 1.5 Flash | For Q&A, docs, code editing |
| Code Parsing | Tree-sitter | 150 lines/chunk, 10 overlap |
| Vector Search | In-memory cosine similarity | Threshold > 0.6 |
| Object Storage | Google Cloud Storage | Two buckets (raw + processed) |
| Database | Firestore | User data, webhooks, workspaces |
| Pipeline Tracking | DVC | 6-stage pipeline, GCS remote |
| Testing | pytest | 69 tests, mocked fixtures |
| Python | 3.11 | Required version |

---

## 8. Troubleshooting

### "401 Unauthorized" on any endpoint

Your GitHub token is expired or missing the `repo` scope. Verify with:

```bash
curl -H "Authorization: token YOUR_GITHUB_TOKEN" https://api.github.com/user
```

If this fails, generate a new token (Step 2).

### Pipeline runs but returns empty results

The repo may not contain supported source files. Tree-sitter supports: Python, JavaScript, TypeScript, Java, Go, Rust, C, C++, Ruby, PHP, C#, Kotlin, Swift, and Scala.

### "Region mismatch" or embedding errors

The Vertex AI region must be `us-east1`. If running DVC locally, confirm:

```bash
echo $VERTEX_LOCATION   # Must output: us-east1
```

### DVC `logs/` directory error

If DVC fails with a missing directory:

```bash
mkdir -p Data-Pipeline/logs Data-Pipeline/data/raw Data-Pipeline/data/processed
```

### Python version conflicts (DVC local only)

Python 3.13 causes `google.cloud` namespace conflicts. Verify you're on 3.11:

```bash
python --version   # Must be 3.11.x
```

### Slow first run on a large repo

The first pipeline run downloads and processes all files. For large repos (1000+ files), this can take 3–5 minutes. Subsequent runs are incremental and much faster.

### Test failures (local only)

Ensure you're using Python 3.11 in a fresh venv:

```bash
cd otto/Data-Pipeline
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

Tests use mocked fixtures — no live API credentials are required.

---

## 9. Quick Reference — Complete Test Sequence

For a full end-to-end test of the deployed pipeline, run these commands in order with any repo you have access to:

```bash
# 1. Verify service is running
curl https://ingest-service-484671782718.us-east1.run.app/health

# 2. Run the full pipeline (ingest + chunk + embed + validate)
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"repo_full_name": "owner/repo", "github_token": "YOUR_GITHUB_TOKEN", "force_reembed": false}'

# 3. Check pipeline status
curl https://ingest-service-484671782718.us-east1.run.app/pipeline/repos/owner/repo/status

# 4. Ask a question about the codebase (RAG Q&A)
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/ask \
  -H "Content-Type: application/json" \
  -d '{"repo_full_name": "owner/repo", "question": "What does this project do?", "github_token": "YOUR_GITHUB_TOKEN"}'

# 5. Semantic code search
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/search \
  -H "Content-Type: application/json" \
  -d '{"repo_full_name": "owner/repo", "query": "main function entry point", "top_k": 5}'

# 6. Generate documentation for a file
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/docs/generate \
  -H "Content-Type: application/json" \
  -d '{"repo_full_name": "owner/repo", "target": "README.md", "doc_type": "readme", "github_token": "YOUR_GITHUB_TOKEN", "push_to_github": false}'

# 7. Force re-embed (clear and regenerate all embeddings)
curl -X POST https://ingest-service-484671782718.us-east1.run.app/pipeline/embed \
  -H "Content-Type: application/json" \
  -d '{"repo_full_name": "owner/repo", "force_reembed": true}'
```

---

**Questions or issues?** Contact the team via GitHub: [github.com/otto-pm](https://github.com/otto-pm)
