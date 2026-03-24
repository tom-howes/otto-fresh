"""
Model Validation Script
Runs a fixed set of held-out test queries against Otto's live RAG endpoint
and computes RAGAS faithfulness and answer relevancy scores.
Fails with exit code 1 if any metric falls below defined thresholds.
Results are logged to experiments/experiments.jsonl.

Usage:
    cd ml-evaluation
    python run_validation.py

Requirements:
    pip install -r requirements.txt
"""
import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ── Config ─────────────────────────────────────────────────────────────────────

INGEST_SERVICE_URL = "https://ingest-service-484671782718.us-east1.run.app"
REPO = "otto-pm/otto"
EXPERIMENTS_LOG = os.path.join(os.path.dirname(__file__), "experiments", "experiments.jsonl")

FAITHFULNESS_THRESHOLD = 0.5
ANSWER_RELEVANCY_THRESHOLD = 0.7

# ── Held-out validation queries ────────────────────────────────────────────────

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

VALIDATION_QUERIES = [
    {
        "id": "val_1",
        "question": "What embedding model and batch size does the ChunkEmbedder use?",
        "type": "answerable",
    },
    {
        "id": "val_2",
        "question": "How does Otto's GitHub OAuth callback work?",
        "type": "answerable",
    },
    {
        "id": "val_3",
        "question": "How does Otto authenticate users with GitHub?",
        "type": "answerable",
    },
    {
        "id": "val_4",
        "question": "What payment provider does Otto use for billing?",
        "type": "not_in_codebase",
    },
    {
        "id": "val_5",
        "question": "How does the RAG service retrieve relevant code chunks for a query?",
        "type": "answerable",
    },
]

# ── Query the RAG endpoint ─────────────────────────────────────────────────────

def query_rag(question: str) -> dict:
    try:
        response = requests.post(
            f"{INGEST_SERVICE_URL}/pipeline/ask",
            json={
                "repo_full_name": REPO,
                "question": question,
                "github_token": GITHUB_TOKEN,
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {"answer": "", "sources": [], "chunks_used": 0}


# ── RAGAS Evaluation ───────────────────────────────────────────────────────────

def run_ragas_evaluation(queries: list, results: list) -> dict:
    try:
        import asyncio
        import litellm
        from ragas.metrics.collections import Faithfulness, AnswerRelevancy
        from ragas.llms import llm_factory
        from ragas.embeddings import GoogleEmbeddings
        import google.generativeai as genai

        project_id = os.getenv("GCP_PROJECT_ID", "otto-pm")
        location = os.getenv("GCP_REGION", "us-east1")

        print("\n🔧 Initialising RAGAS with Vertex AI...")
        os.environ["VERTEXAI_PROJECT"] = project_id
        os.environ["VERTEXAI_LOCATION"] = location

        llm = llm_factory(
            "vertex_ai/gemini-2.5-flash-lite",
            provider="litellm",
            client=litellm.acompletion,
            max_tokens=8192
        )

        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        embeddings = GoogleEmbeddings(client=genai, model="gemini-embedding-001")

        faithfulness_metric = Faithfulness(llm=llm)
        relevancy_metric = AnswerRelevancy(llm=llm, embeddings=embeddings)

        async def score_all():
            faith_scores = []
            rel_scores = []
            for q, r in zip(queries, results):
                contexts = [s.get("content", "") for s in r.get("sources", []) if s.get("content")]
                if not contexts:
                    contexts = ["no context retrieved"]
                answer = r.get("answer", "")
                if not answer or answer.startswith("Error:"):
                    continue
                f = await faithfulness_metric.ascore(
                    user_input=q["question"],
                    response=answer,
                    retrieved_contexts=contexts
                )
                rv = await relevancy_metric.ascore(
                    user_input=q["question"],
                    response=answer
                )
                faith_scores.append(f.value)
                rel_scores.append(rv.value)
                print(f"  ✓ [{q['id']}] faithfulness={f.value:.3f}, relevancy={rv.value:.3f}")
            return faith_scores, rel_scores

        print("📊 Running RAGAS evaluation...")
        faith_scores, rel_scores = asyncio.run(score_all())

        if not faith_scores:
            print("⚠️  No valid scores produced")
            return {"faithfulness": None, "answer_relevancy": None}

        return {
            "faithfulness": round(sum(faith_scores) / len(faith_scores), 3),
            "answer_relevancy": round(sum(rel_scores) / len(rel_scores), 3),
        }

    except ImportError as e:
        print(f"⚠️  Missing dependency: {e}")
        print("   Run: pip install ragas google-generativeai litellm")
        return {"faithfulness": None, "answer_relevancy": None}
    except Exception as e:
        print(f"⚠️  RAGAS evaluation failed: {e}")
        return {"faithfulness": None, "answer_relevancy": None}


# ── Log to experiments.jsonl ───────────────────────────────────────────────────

def log_run(run_data: dict):
    with open(EXPERIMENTS_LOG, "a") as f:
        f.write(json.dumps(run_data) + "\n")
    print(f"📝 Logged to {EXPERIMENTS_LOG}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"🔍 OTTO MODEL VALIDATION")
    print(f"{'='*60}")
    print(f"Endpoint: {INGEST_SERVICE_URL}")
    print(f"Repo:     {REPO}")
    print(f"Queries:  {len(VALIDATION_QUERIES)}")
    print(f"Thresholds: faithfulness ≥ {FAITHFULNESS_THRESHOLD}, "
          f"answer_relevancy ≥ {ANSWER_RELEVANCY_THRESHOLD}")

    results = []
    for i, q in enumerate(VALIDATION_QUERIES, 1):
        print(f"\n[{i}/{len(VALIDATION_QUERIES)}] {q['question']}")
        result = query_rag(q["question"])
        results.append(result)
        print(f"  ✓ Answer: {result.get('answer', '')[:100]}...")
        print(f"  ✓ Chunks used: {result.get('chunks_used', 0)}")

    scores = run_ragas_evaluation(VALIDATION_QUERIES, results)

    print(f"\n{'='*60}")
    print(f"📊 VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Faithfulness:     {scores['faithfulness']} "
          f"(threshold: {FAITHFULNESS_THRESHOLD})")
    print(f"Answer Relevancy: {scores['answer_relevancy']} "
          f"(threshold: {ANSWER_RELEVANCY_THRESHOLD})")

    passed = True
    if scores["faithfulness"] is None or scores["answer_relevancy"] is None:
        print("❌ FAILED: RAGAS evaluation did not produce scores — cannot validate")
        passed = False
    else:
        if scores["faithfulness"] < FAITHFULNESS_THRESHOLD:
            print(f"❌ FAILED: Faithfulness below threshold")
            passed = False
        if scores["answer_relevancy"] < ANSWER_RELEVANCY_THRESHOLD:
            print(f"❌ FAILED: Answer relevancy below threshold")
            passed = False

    if passed:
        print(f"✅ VALIDATION PASSED")
    else:
        print(f"❌ VALIDATION FAILED")

    if scores["faithfulness"] is not None:
        log_run({
            "timestamp": datetime.now().isoformat(),
            "run_type": "validation",
            "prompt_version": "V4",
            "temperature": 0.2,
            "top_k": 8,
            "guardrails": ["answer_only_from_context", "say_so_if_not_in_context"],
            "endpoint": INGEST_SERVICE_URL,
            "repo": REPO,
            "num_queries": len(VALIDATION_QUERIES),
            "scores": scores,
            "passed": passed,
            "thresholds": {
                "faithfulness": FAITHFULNESS_THRESHOLD,
                "answer_relevancy": ANSWER_RELEVANCY_THRESHOLD,
            }
        })
    else:
        print("⚠️  Skipping log — no valid scores produced")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()