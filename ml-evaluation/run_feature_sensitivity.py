"""
Feature / Input Sensitivity Analysis
Tests two things:
  1. Context degradation — how faithfulness changes with top_k=1, 3, 8
  2. Query rephrasing — how score varies across 3 wordings of the same question

Results logged to experiments/experiments.jsonl.
Run plot_feature_sensitivity.py separately to generate charts.

Usage:
    cd ml-evaluation
    python run_feature_sensitivity.py                  # run both tests
    python run_feature_sensitivity.py --test context   # context degradation only
    python run_feature_sensitivity.py --test rephrasing # query rephrasing only

Output:
    experiments/experiments.jsonl  — one entry per configuration
"""
import os
import json
import asyncio
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── Config ──────────────────────────────────────────────────────────────────────

INGEST_SERVICE_URL = "https://ingest-service-484671782718.us-east1.run.app"
REPO = "otto-pm/otto"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
EXPERIMENTS_LOG = os.path.join(os.path.dirname(__file__), "experiments", "experiments.jsonl")

FAITHFULNESS_THRESHOLD = 0.5
RELEVANCY_THRESHOLD = 0.7

# ── Context degradation — same queries as sensitivity, varying top_k ────────────
# top_k=3, 5, 8, 12 already exist in experiments.jsonl from run_sensitivity.py
# No additional runs needed — plot_feature_sensitivity.py reads directly from log

CONTEXT_QUERIES = []  # unused — context degradation reads from experiments.jsonl

CONTEXT_TOPK_VALUES = []  # all values already logged

# ── Query rephrasing — 3 wordings of the same question ──────────────────────────

REPHRASING_QUERIES = [
    {"id": "rephrase_1", "question": "How does the RAG service retrieve relevant code chunks for a query?"},
    {"id": "rephrase_2", "question": "What method does Otto use to find the most relevant code snippets when answering a question?"},
    {"id": "rephrase_3", "question": "Can you explain the chunk retrieval process in Otto's question answering pipeline?"},
]

# ── Query RAG ────────────────────────────────────────────────────────────────────

def query_rag(question: str, temperature: float = 0.2, top_k: int = 8) -> dict:
    try:
        response = requests.post(
            f"{INGEST_SERVICE_URL}/pipeline/ask",
            json={
                "repo_full_name": REPO,
                "question": question,
                "github_token": GITHUB_TOKEN,
                "temperature": temperature,
                "top_k": top_k,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    ❌ Request failed: {e}")
        return {"answer": "", "sources": [], "chunks_used": 0}


# ── RAGAS ────────────────────────────────────────────────────────────────────────

def run_ragas(queries: list, results: list) -> dict:
    try:
        import litellm
        from ragas.metrics.collections import Faithfulness, AnswerRelevancy
        from ragas.llms import llm_factory
        from ragas.embeddings import GoogleEmbeddings
        import google.generativeai as genai

        project_id = os.getenv("GCP_PROJECT_ID", "otto-pm")
        location = os.getenv("GCP_REGION", "us-east1")
        os.environ["VERTEXAI_PROJECT"] = project_id
        os.environ["VERTEXAI_LOCATION"] = location

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("    ⚠️  GEMINI_API_KEY not set")
            return {"faithfulness": None, "answer_relevancy": None}

        llm = llm_factory(
            "vertex_ai/gemini-2.5-flash-lite",
            provider="litellm",
            client=litellm.acompletion,
            max_tokens=8192
        )
        genai.configure(api_key=api_key)
        emb = GoogleEmbeddings(client=genai, model="gemini-embedding-001")

        faithfulness_metric = Faithfulness(llm=llm)
        relevancy_metric = AnswerRelevancy(llm=llm, embeddings=emb)

        async def score_all():
            faith_scores, rel_scores = [], []
            for q, r in zip(queries, results):
                answer = r.get("answer", "")
                if not answer or answer.startswith("Error:"):
                    continue
                contexts = [s.get("content", "") for s in r.get("sources", []) if s.get("content")]
                if not contexts:
                    contexts = ["no context retrieved"]
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
                print(f"    ✓ [{q['id']}] faithfulness={f.value:.3f}, relevancy={rv.value:.3f}")
            return faith_scores, rel_scores

        faith_scores, rel_scores = asyncio.run(score_all())

        if not faith_scores:
            print("    ⚠️  No valid scores produced")
            return {"faithfulness": None, "answer_relevancy": None}

        return {
            "faithfulness": round(sum(faith_scores) / len(faith_scores), 3),
            "answer_relevancy": round(sum(rel_scores) / len(rel_scores), 3),
        }

    except Exception as e:
        print(f"    ⚠️  RAGAS failed: {e}")
        return {"faithfulness": None, "answer_relevancy": None}


# ── Log ──────────────────────────────────────────────────────────────────────────

def log_run(entry: dict):
    os.makedirs(os.path.dirname(EXPERIMENTS_LOG), exist_ok=True)
    with open(EXPERIMENTS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ── Tests ─────────────────────────────────────────────────────────────────────────

def run_context_degradation():
    print(f"\n── Context Degradation ──")
    print(f"   top_k=3, 5, 8, 12 already logged from run_sensitivity.py")
    print(f"   No additional runs needed — plot_feature_sensitivity.py reads from experiments.jsonl")


def run_rephrasing():
    print(f"\n── Query Rephrasing Test ──")
    print(f"   Base question: '{REPHRASING_QUERIES[0]['question']}'")

    results = []
    for q in REPHRASING_QUERIES:
        print(f"\n  [{q['id']}] {q['question']}")
        r = query_rag(q["question"], temperature=0.2, top_k=8)
        results.append(r)
        print(f"    ✓ {r.get('answer', '')[:80]}...")

    print(f"\n  📊 Running RAGAS...")
    scores = run_ragas(REPHRASING_QUERIES, results)
    print(f"  → faithfulness={scores['faithfulness']}, relevancy={scores['answer_relevancy']}")

    if scores["faithfulness"] is not None:
        log_run({
            "timestamp": datetime.now().isoformat(),
            "run_type": "feature_sensitivity_rephrasing",
            "prompt_version": "V4",
            "temperature": 0.2,
            "top_k": 8,
            "num_queries": len(REPHRASING_QUERIES),
            "queries": [q["question"] for q in REPHRASING_QUERIES],
            "scores": scores,
            "thresholds": {
                "faithfulness": FAITHFULNESS_THRESHOLD,
                "answer_relevancy": RELEVANCY_THRESHOLD,
            },
        })
    else:
        print("  ⚠️  Skipping log — no valid scores produced")


# ── Main ─────────────────────────────────────────────────────────────────────────

def main(test=None):
    print(f"\n{'='*60}")
    print("🔬 OTTO — FEATURE / INPUT SENSITIVITY ANALYSIS")
    print(f"{'='*60}")

    if test in (None, "context"):
        run_context_degradation()

    if test in (None, "rephrasing"):
        run_rephrasing()

    print(f"\n✅ Results logged to {EXPERIMENTS_LOG}")
    print("   Run plot_feature_sensitivity.py to generate charts.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str, default=None,
                        choices=["context", "rephrasing"],
                        help="Run only one test: 'context' or 'rephrasing'")
    args = parser.parse_args()
    main(test=args.test)