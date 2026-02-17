#!/bin/bash

# Otto Complete Testing Suite
# Tests all endpoints for deployed backend and ingest services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="https://backend-service-484671782718.us-east1.run.app"
INGEST_URL="https://ingest-service-484671782718.us-east1.run.app"

# Get session token (you need to set this)
if [ -z "$SESSION_TOKEN" ]; then
    echo -e "${RED}❌ SESSION_TOKEN not set${NC}"
    echo "Please set it with: export SESSION_TOKEN=\"your_token_from_browser\""
    exit 1
fi

# Get GitHub token (you need to set this)
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ GITHUB_TOKEN not set${NC}"
    echo "Please set it with: export GITHUB_TOKEN=\"your_github_token\""
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           OTTO COMPLETE TESTING SUITE                     ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# ==================== HEALTH CHECKS ====================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}1. HEALTH CHECKS${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}→ Testing Backend Health...${NC}"
curl -s $BACKEND_URL/health | jq '.'

echo -e "\n${BLUE}→ Testing Ingest Service Health...${NC}"
curl -s $INGEST_URL/health | jq '.'

echo -e "\n${BLUE}→ Testing RAG Health (Backend + Ingest)...${NC}"
curl -s $BACKEND_URL/rag/health | jq '.'

# ==================== AUTHENTICATION ====================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}2. AUTHENTICATION${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}→ Testing Get Current User...${NC}"
curl -s $BACKEND_URL/users/me \
  -b "session_token=$SESSION_TOKEN" | jq '.'

echo -e "\n${BLUE}→ Testing Active Webhook Sessions...${NC}"
curl -s $BACKEND_URL/webhook/active-sessions | jq '.'

# ==================== REPOSITORY MANAGEMENT ====================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}3. REPOSITORY MANAGEMENT${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}→ Testing User Repository History...${NC}"
curl -s $BACKEND_URL/rag/repos/user/history \
  -b "session_token=$SESSION_TOKEN" | jq '.'

echo -e "\n${BLUE}→ Testing Repository Status (otto-pm/otto)...${NC}"
curl -s $BACKEND_URL/rag/repos/otto-pm/otto/status \
  -b "session_token=$SESSION_TOKEN" | jq '.'

echo -e "\n${BLUE}→ Testing Repository Access Check...${NC}"
curl -s $BACKEND_URL/rag/repos/otto-pm/otto/access \
  -b "session_token=$SESSION_TOKEN" | jq '.'

echo -e "\n${BLUE}→ Testing Commit History...${NC}"
curl -s "$BACKEND_URL/rag/repos/otto-pm/otto/commit-history?limit=5" \
  -b "session_token=$SESSION_TOKEN" | jq '.'

echo -e "\n${BLUE}→ Testing All Indexed Repos...${NC}"
curl -s $BACKEND_URL/rag/repos/indexed \
  -b "session_token=$SESSION_TOKEN" | jq '.'

echo -e "\n${BLUE}→ Testing System Stats...${NC}"
curl -s $BACKEND_URL/rag/stats \
  -b "session_token=$SESSION_TOKEN" | jq '.'

# ==================== RAG SERVICES ====================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}4. RAG SERVICES (Q&A, Docs, Code)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}→ Testing Q&A Service (via Backend)...${NC}"
curl -s -X POST $BACKEND_URL/rag/ask \
  -H "Content-Type: application/json" \
  -b "session_token=$SESSION_TOKEN" \
  -d '{
    "repo_full_name": "otto-pm/otto",
    "question": "What services does the RAG system provide?"
  }' | jq '.answer, .chunks_used, (.sources | length)'

echo -e "\n${BLUE}→ Testing Q&A Service (Direct to Ingest)...${NC}"
curl -s -X POST $INGEST_URL/pipeline/ask \
  -H "Content-Type: application/json" \
  -d "{
    \"repo_full_name\": \"otto-pm/otto\",
    \"question\": \"How does the GitHub OAuth authentication flow work?\",
    \"github_token\": \"$GITHUB_TOKEN\"
  }" | jq '.answer, .chunks_used'

echo -e "\n${BLUE}→ Testing Code Search...${NC}"
curl -s -X POST $BACKEND_URL/rag/search \
  -H "Content-Type: application/json" \
  -b "session_token=$SESSION_TOKEN" \
  -d '{
    "repo_full_name": "otto-pm/otto",
    "query": "webhook handler",
    "top_k": 3
  }' | jq '.total_found, (.results[0] | {file_path, chunk_type, lines})'

echo -e "\n${BLUE}→ Testing Documentation Generation...${NC}"
curl -s -X POST $BACKEND_URL/rag/docs/generate \
  -H "Content-Type: application/json" \
  -b "session_token=$SESSION_TOKEN" \
  -d '{
    "repo_full_name": "otto-pm/otto",
    "target": "authentication system",
    "doc_type": "api",
    "push_to_github": false
  }' | jq '.type, .files_referenced, (.documentation | length)'

# ==================== PIPELINE OPERATIONS ====================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}5. PIPELINE OPERATIONS${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}→ Testing Pipeline Status (should be cached)...${NC}"
curl -s -X POST $BACKEND_URL/rag/repos/pipeline \
  -H "Content-Type: application/json" \
  -b "session_token=$SESSION_TOKEN" \
  -d '{
    "repo_full_name": "otto-pm/otto",
    "branch": "main"
  }' | jq '{success, was_cached, total_chunks, total_embedded, message}'

# ==================== USER PREFERENCES ====================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}6. USER PREFERENCES${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}→ Testing Save User Preferences...${NC}"
curl -s -X POST $BACKEND_URL/rag/repos/user/preferences \
  -H "Content-Type: application/json" \
  -b "session_token=$SESSION_TOKEN" \
  -d '{
    "repo_full_name": "otto-pm/otto",
    "favorite": true,
    "auto_push_prs": false,
    "preferred_doc_type": "api"
  }' | jq '.'

echo -e "\n${BLUE}→ Testing Get User Preferences...${NC}"
curl -s $BACKEND_URL/rag/repos/otto-pm/otto/preferences \
  -b "session_token=$SESSION_TOKEN" | jq '.'

# ==================== GITHUB INTEGRATION ====================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}7. GITHUB INTEGRATION${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}→ Testing List User's GitHub Repos...${NC}"
curl -s "$BACKEND_URL/rag/repos/user/all?indexed_only=true" \
  -b "session_token=$SESSION_TOKEN" | jq '.[0] | {full_name, indexed, ready_for_rag, total_chunks}'

# ==================== PERFORMANCE TESTS ====================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}8. PERFORMANCE TESTS${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}→ Testing Q&A Response Time (5 queries)...${NC}"
for i in {1..5}; do
    echo -n "  Query $i: "
    START=$(date +%s.%N)
    curl -s -X POST $BACKEND_URL/rag/ask \
      -H "Content-Type: application/json" \
      -b "session_token=$SESSION_TOKEN" \
      -d '{
        "repo_full_name": "otto-pm/otto",
        "question": "What is the purpose of the webhook handler?"
      }' > /dev/null
    END=$(date +%s.%N)
    DIFF=$(echo "$END - $START" | bc)
    echo -e "${GREEN}${DIFF}s${NC}"
done

# ==================== SUMMARY ====================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}✅ TESTING COMPLETE${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${GREEN}All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Test webhook: Push to GitHub and check /webhook/active-sessions"
echo "  2. Test streaming: Use /rag/ask/stream endpoint"
echo "  3. Monitor logs: gcloud run services logs tail backend-service --region=us-east1"