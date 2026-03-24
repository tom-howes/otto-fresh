"""
Sensitivity Analysis
Tests how output quality varies with temperature and top-k chunk count.
Uses the final prompt (V4) and a fixed query set.
Results logged to experiments/experiments.jsonl.
Run plot_sensitivity.py separately to generate charts.

Usage:
    cd ml-evaluation
    python run_sensitivity.py                          # run all sweeps
    python run_sensitivity.py --sweep temperature     # run temperature sweep only
    python run_sensitivity.py --sweep topk            # run top-k sweep only

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

TEMPERATURE_VALUES = [0.0, 0.2, 0.5, 0.8]
TOPK_VALUES = [3, 5, 8, 12]

V4_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about a GitHub codebase. "
    "Answer ONLY using information from the provided code context. "
    "If the answer cannot be found in the context, say: "
    "'I don't have enough information in the codebase to answer that.' "
    "Do not speculate or use outside knowledge. "
    "Structure your answer clearly: start with a direct answer, "
    "then explain with reference to specific files or functions if relevant."
)

SENSITIVITY_QUERIES = [
    {"id": "s1", "question": "What embedding model and batch size does the ChunkEmbedder use?"},
    {"id": "s2", "question": "How does Otto authenticate users with GitHub?"},
    {"id": "s3", "question": "How does the RAG service retrieve relevant code chunks for a query?"},
    {"id": "s4", "question": "What does the EnhancedCodeChunker add compared to the base CodeChunker?"},
    {"id": "s5", "question": "What payment provider does Otto use for billing?"},
]

# ── Query RAG ────────────────────────────────────────────────────────────────────

def query_rag(question: str, temperature: float, top_k: int) -> dict:
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


# ── Sweep ────────────────────────────────────────────────────────────────────────

def run_sweep(sweep_param: str, values: list, fixed_temp: float = None, fixed_topk: int = None):
    print(f"\n── {sweep_param} sweep ──")
    print(f"   Testing: {values}")

    for val in values:
        temp = val if sweep_param == "temperature" else fixed_temp
        topk = val if sweep_param == "top_k" else fixed_topk
        print(f"\n  {sweep_param}={val} (temperature={temp}, top_k={topk})")

        results = []
        for q in SENSITIVITY_QUERIES:
            print(f"    [{q['id']}] {q['question'][:60]}...")
            r = query_rag(q["question"], temp, topk)
            results.append(r)
            print(f"      ✓ {r.get('answer', '')[:60]}...")

        print(f"    📊 Running RAGAS...")
        scores = run_ragas(SENSITIVITY_QUERIES, results)
        print(f"    → faithfulness={scores['faithfulness']}, relevancy={scores['answer_relevancy']}")

        if scores["faithfulness"] is not None:
            log_run({
                "timestamp": datetime.now().isoformat(),
                "run_type": "sensitivity",
                "sweep_param": sweep_param,
                "sweep_value": val,
                "prompt_version": "V4",
                "temperature": temp,
                "top_k": topk,
                "num_queries": len(SENSITIVITY_QUERIES),
                "scores": scores,
                "thresholds": {
                    "faithfulness": FAITHFULNESS_THRESHOLD,
                    "answer_relevancy": RELEVANCY_THRESHOLD,
                },
            })
        else:
            print(f"    ⚠️  Skipping log for {sweep_param}={val} — no valid scores produced")


# ── Main ─────────────────────────────────────────────────────────────────────────

def main(sweep=None):
    print(f"\n{'='*60}")
    print("🔬 OTTO — SENSITIVITY ANALYSIS")
    print(f"{'='*60}")
    print(f"Prompt version: V4 (final)")
    print(f"Queries per config: {len(SENSITIVITY_QUERIES)}")

    if sweep in (None, "temperature"):
        run_sweep("temperature", TEMPERATURE_VALUES, fixed_topk=8)

    if sweep in (None, "top_k"):
        run_sweep("top_k", TOPK_VALUES, fixed_temp=0.2)

    print(f"\n✅ Results logged to {EXPERIMENTS_LOG}")
    print("   Run plot_sensitivity.py to generate charts.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", type=str, default=None, choices=["temperature", "topk"],
                        help="Run only one sweep: 'temperature' or 'topk'")
    args = parser.parse_args()
    sweep = "top_k" if args.sweep == "topk" else args.sweep
    main(sweep=sweep)