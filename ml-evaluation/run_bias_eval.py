"""
Bias Evaluation — Slicing by Language, Repo Section, and Chunk Size
Runs RAGAS faithfulness and answer relevancy per slice.
Flags slices scoring more than 1.5 stdev below average.
Outputs structured JSON bias report to reports/bias_report.json.
Run plot_bias.py separately to generate charts.

Usage:
    cd ml-evaluation
    python run_bias_eval.py                                  # run all slices
    python run_bias_eval.py --dimension chunk_size           # run one dimension
    python run_bias_eval.py --dimension chunk_size --slice small  # run one slice

Output:
    reports/bias_report.json
    experiments/experiments.jsonl  — one entry per slice + summary entry
"""
import os
import json
import asyncio
import statistics
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── Config ──────────────────────────────────────────────────────────────────────

INGEST_SERVICE_URL = os.environ.get("INGEST_SERVICE_URL", "https://ingest-service-484671782718.us-east1.run.app")
REPO = os.environ.get("EVAL_REPO", "otto-pm/otto")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
EXPERIMENTS_LOG = os.path.join(os.path.dirname(__file__), "experiments", "experiments.jsonl")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)

FAITHFULNESS_THRESHOLD = 0.5
RELEVANCY_THRESHOLD = 0.7
FLAG_STDEV_MULTIPLIER = 1.5  # slices must be notably below average to flag

# ── Slices and their queries ─────────────────────────────────────────────────────

SLICES = {
    "language": {
        "Python": [
            {"id": "lang_py_1", "question": "What embedding model and batch size does the ChunkEmbedder use?"},
            {"id": "lang_py_2", "question": "How does the SchemaValidator check chunk structure?"},
            {"id": "lang_py_3", "question": "How does the ChunkEmbedder handle batches that fail during embedding?"},
        ],
        "TypeScript": [
            {"id": "lang_ts_1", "question": "How does the frontend handle GitHub OAuth login?"},
            {"id": "lang_ts_2", "question": "What API routes does the Next.js frontend expose?"},
            {"id": "lang_ts_3", "question": "How does the frontend display Q&A results to the user?"},
        ],
    },
    "repo_section": {
        "frontend": [
            {"id": "sec_fe_1", "question": "How does the frontend handle GitHub OAuth login?"},
            {"id": "sec_fe_2", "question": "What does the main page component render?"},
        ],
        "backend": [
            {"id": "sec_be_1", "question": "How does Otto authenticate users with GitHub?"},
            {"id": "sec_be_2", "question": "How does the backend expose the Q&A endpoint?"},
        ],
        "Data-Pipeline": [
            {"id": "sec_dp_1", "question": "What embedding model and batch size does the ChunkEmbedder use?"},
            {"id": "sec_dp_2", "question": "How does the AnomalyDetector identify outlier chunks?"},
        ],
        "infrastructure": [
            {"id": "sec_inf_1", "question": "How is the ingest service deployed to Cloud Run?"},
            {"id": "sec_inf_2", "question": "What GCP services does Otto's Terraform configuration provision?"},
        ],
    },
    "chunk_size": {
        "small": [
            {"id": "size_sm_1", "question": "How does the ChunkEmbedder batch chunks when calling the Vertex AI embedding API?"},
            {"id": "size_sm_2", "question": "What fields does the SchemaValidator check on each chunk?"},
        ],
        "medium": [
            {"id": "size_md_1", "question": "How does Otto authenticate users with GitHub?"},
            {"id": "size_md_2", "question": "How does the RAG service retrieve relevant code chunks for a query?"},
        ],
        "large": [
            {"id": "size_lg_1", "question": "Explain the full ingest-chunk-embed-validate pipeline in detail."},
            {"id": "size_lg_2", "question": "How does EnhancedCodeChunker extract metadata from Python files?"},
        ],
    },
}

# ── Query RAG ────────────────────────────────────────────────────────────────────

def query_rag(question: str) -> dict:
    try:
        response = requests.post(
            f"{INGEST_SERVICE_URL}/pipeline/ask",
            json={
                "repo_full_name": REPO,
                "question": question,
                "github_token": GITHUB_TOKEN,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    Request failed: {e}")
        return {"answer": "", "sources": [], "chunks_used": 0}


# ── RAGAS per slice ───────────────────────────────────────────────────────────────

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
            print("    GEMINI_API_KEY not set")
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
                print(f"    [{q['id']}] faithfulness={f.value:.3f}, relevancy={rv.value:.3f}")
            return faith_scores, rel_scores

        faith_scores, rel_scores = asyncio.run(score_all())

        if not faith_scores:
            print("    No valid scores produced")
            return {"faithfulness": None, "answer_relevancy": None}

        return {
            "faithfulness": round(sum(faith_scores) / len(faith_scores), 3),
            "answer_relevancy": round(sum(rel_scores) / len(rel_scores), 3),
        }

    except Exception as e:
        print(f"    RAGAS failed: {e}")
        return {"faithfulness": None, "answer_relevancy": None}


# ── Flag biased slices ────────────────────────────────────────────────────────────

def flag_biased_slices(slice_scores: dict) -> tuple:
    faith_vals = [s["faithfulness"] for s in slice_scores.values() if s["faithfulness"] is not None]
    rel_vals = [s["answer_relevancy"] for s in slice_scores.values() if s["answer_relevancy"] is not None]

    if len(faith_vals) < 2:
        return {}, {"faithfulness_mean": None, "relevancy_mean": None,
                    "faithfulness_stdev": None, "relevancy_stdev": None}

    faith_mean = statistics.mean(faith_vals)
    faith_stdev = statistics.stdev(faith_vals)
    rel_mean = statistics.mean(rel_vals)
    rel_stdev = statistics.stdev(rel_vals) if len(rel_vals) > 1 else 0.0

    flagged = {}
    for name, scores in slice_scores.items():
        reasons = []
        if scores["faithfulness"] is not None and scores["faithfulness"] < faith_mean - FLAG_STDEV_MULTIPLIER * faith_stdev:
            reasons.append(
                f"faithfulness {scores['faithfulness']:.3f} < mean-1.5stdev "
                f"({faith_mean - FLAG_STDEV_MULTIPLIER * faith_stdev:.3f})"
            )
        if scores["answer_relevancy"] is not None and scores["answer_relevancy"] < rel_mean - FLAG_STDEV_MULTIPLIER * rel_stdev:
            reasons.append(
                f"relevancy {scores['answer_relevancy']:.3f} < mean-1.5stdev "
                f"({rel_mean - FLAG_STDEV_MULTIPLIER * rel_stdev:.3f})"
            )
        if reasons:
            flagged[name] = reasons

    stats = {
        "faithfulness_mean": round(faith_mean, 3),
        "faithfulness_stdev": round(faith_stdev, 3),
        "relevancy_mean": round(rel_mean, 3),
        "relevancy_stdev": round(rel_stdev, 3),
    }
    return flagged, stats


# ── Log ───────────────────────────────────────────────────────────────────────────

def log_run(entry: dict):
    os.makedirs(os.path.dirname(EXPERIMENTS_LOG), exist_ok=True)
    with open(EXPERIMENTS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────────

def main(slices=None):
    if slices is None:
        slices = SLICES
    print(f"\n{'='*60}")
    print("OTTO — BIAS EVALUATION")
    print(f"{'='*60}")

    bias_report = {
        "timestamp": datetime.now().isoformat(),
        "prompt_version": "V4",
        "dimensions": {},
        "bias_detected": False,
        "flagged_slices": [],
        "mitigation": [],
    }

    for dimension, slices_in_dim in slices.items():
        print(f"\n-- Dimension: {dimension} --")
        slice_scores = {}

        for slice_name, queries in slices_in_dim.items():
            print(f"\n  Slice: {slice_name} ({len(queries)} queries)")
            results = []
            for q in queries:
                print(f"    [{q['id']}] {q['question'][:60]}...")
                r = query_rag(q["question"])
                results.append(r)
                print(f"      {r.get('answer', '')[:60]}...")

            print(f"    Running RAGAS for {slice_name}...")
            scores = run_ragas(queries, results)
            slice_scores[slice_name] = scores
            print(f"    -> faithfulness={scores['faithfulness']}, relevancy={scores['answer_relevancy']}")

            if scores["faithfulness"] is not None:
                log_run({
                    "timestamp": datetime.now().isoformat(),
                    "run_type": "bias_eval",
                    "dimension": dimension,
                    "slice": slice_name,
                    "prompt_version": "V4",
                    "temperature": 0.2,
                    "top_k": 8,
                    "num_queries": len(queries),
                    "scores": scores,
                    "thresholds": {
                        "faithfulness": FAITHFULNESS_THRESHOLD,
                        "answer_relevancy": RELEVANCY_THRESHOLD,
                    },
                })
            else:
                print(f"    Skipping log for {slice_name} — no valid scores produced")

        flagged, stats = flag_biased_slices(slice_scores)

        bias_report["dimensions"][dimension] = {
            "slices": {
                name: {
                    "faithfulness": s["faithfulness"],
                    "answer_relevancy": s["answer_relevancy"],
                    "flagged": name in flagged,
                    "flag_reasons": flagged.get(name, []),
                }
                for name, s in slice_scores.items()
            },
            "stats": stats,
            "flagged_slices": list(flagged.keys()),
        }

        if flagged:
            bias_report["bias_detected"] = True
            for name, reasons in flagged.items():
                bias_report["flagged_slices"].append({
                    "dimension": dimension,
                    "slice": name,
                    "reasons": reasons,
                })

        print(f"\n  Stats: faithfulness mean={stats['faithfulness_mean']}, "
              f"stdev={stats['faithfulness_stdev']}")
        if flagged:
            print(f"  Flagged: {list(flagged.keys())}")
        else:
            print(f"  No bias detected in {dimension} dimension")

    # ── Mitigation recommendations ────────────────────────────────────────────────
    for item in bias_report["flagged_slices"]:
        dim, slc = item["dimension"], item["slice"]
        if dim == "language":
            rec = (f"Force re-embed {slc} chunks: run embedder.py with "
                   f"force_reembed=True filtering to language='{slc}'")
        elif dim == "repo_section":
            rec = (f"Check chunk count for '{slc}' in chunks_embedded.jsonl. "
                   f"If underrepresented, re-run pipeline with expanded file coverage.")
        else:
            rec = (f"Review chunking strategy for '{slc}' chunks — "
                   f"consider adjusting chunk size boundaries.")
        bias_report["mitigation"].append({"dimension": dim, "slice": slc, "recommendation": rec})

    # ── Save report ───────────────────────────────────────────────────────────────
    report_path = os.path.join(REPORTS_DIR, "bias_report.json")
    with open(report_path, "w") as f:
        json.dump(bias_report, f, indent=2)
    print(f"\nBias report saved to {report_path}")

    # ── Log summary (only if at least one slice scored successfully) ──────────────
    all_scores = [
        s
        for dim in bias_report["dimensions"].values()
        for s in dim["slices"].values()
        if s["faithfulness"] is not None
    ]
    if not all_scores:
        print("Skipping summary log — no valid scores produced")
        return

    log_run({
        "timestamp": datetime.now().isoformat(),
        "run_type": "bias_eval_summary",
        "prompt_version": "V4",
        "bias_detected": bias_report["bias_detected"],
        "flagged_slices": bias_report["flagged_slices"],
        "dimensions_evaluated": list(slices.keys()),
    })

    # ── Final summary ─────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("BIAS EVALUATION SUMMARY")
    print(f"{'='*60}")
    if bias_report["bias_detected"]:
        print("BIAS DETECTED in the following slices:")
        for item in bias_report["flagged_slices"]:
            print(f"  [{item['dimension']}] {item['slice']}: {'; '.join(item['reasons'])}")
        print(f"\nMitigation recommendations saved to {report_path}")
    else:
        print("No bias detected across all slices and dimensions.")

    print(f"\nRun plot_bias.py to generate charts.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dimension", type=str, default=None,
                        help="Only run a specific dimension (e.g. chunk_size)")
    parser.add_argument("--slice", type=str, default=None,
                        help="Only run a specific slice (e.g. small). Requires --dimension.")
    args = parser.parse_args()

    if args.dimension:
        if args.dimension not in SLICES:
            print(f"Unknown dimension '{args.dimension}'. Options: {list(SLICES.keys())}")
        elif args.slice:
            if args.slice not in SLICES[args.dimension]:
                print(f"Unknown slice '{args.slice}'. Options: {list(SLICES[args.dimension].keys())}")
            else:
                main({args.dimension: {args.slice: SLICES[args.dimension][args.slice]}})
        else:
            main({args.dimension: SLICES[args.dimension]})
    else:
        main()