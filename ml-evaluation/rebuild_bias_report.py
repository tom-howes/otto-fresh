"""
Rebuild Bias Report
Reconstructs reports/bias_report.json from experiments/experiments.jsonl,
taking the most recent run per slice. Run this after partial reruns to
merge new slice results with older ones before plotting.

Usage:
    cd ml-evaluation
    python rebuild_bias_report.py
"""
import os
import json
import statistics

EXPERIMENTS_LOG = os.path.join(os.path.dirname(__file__), "experiments", "experiments.jsonl")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
REPORT_PATH = os.path.join(REPORTS_DIR, "bias_report.json")

FLAG_STDEV_MULTIPLIER = 1.5

os.makedirs(REPORTS_DIR, exist_ok=True)


def load_latest_slice_runs() -> dict:
    """Load experiments.jsonl and return the most recent run per (dimension, slice)."""
    latest = {}
    with open(EXPERIMENTS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            run = json.loads(line)
            if run.get("run_type") != "bias_eval":
                continue
            key = (run["dimension"], run["slice"])
            # Later entries overwrite earlier ones — most recent wins
            latest[key] = run
    return latest


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

    return flagged, {
        "faithfulness_mean": round(faith_mean, 3),
        "faithfulness_stdev": round(faith_stdev, 3),
        "relevancy_mean": round(rel_mean, 3),
        "relevancy_stdev": round(rel_stdev, 3),
    }


def main():
    print(f"\n{'='*50}")
    print("🔧 REBUILD BIAS REPORT")
    print(f"{'='*50}")

    latest_runs = load_latest_slice_runs()
    print(f"✓ Found {len(latest_runs)} slice runs in experiments.jsonl")

    # Group by dimension
    dimensions = {}
    for (dimension, slice_name), run in latest_runs.items():
        dimensions.setdefault(dimension, {})[slice_name] = run["scores"]

    bias_report = {
        "timestamp": max(r["timestamp"] for r in latest_runs.values()),
        "prompt_version": "V4",
        "dimensions": {},
        "bias_detected": False,
        "flagged_slices": [],
        "mitigation": [],
    }

    for dimension, slice_scores in dimensions.items():
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

        print(f"\n  {dimension}:")
        for slice_name, scores in slice_scores.items():
            flag = " ⚠️  FLAGGED" if slice_name in flagged else ""
            print(f"    {slice_name}: faithfulness={scores['faithfulness']}, "
                  f"relevancy={scores['answer_relevancy']}{flag}")

    # Mitigation recommendations
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

    with open(REPORT_PATH, "w") as f:
        json.dump(bias_report, f, indent=2)

    print(f"\n✅ Rebuilt bias report saved to {REPORT_PATH}")
    if bias_report["bias_detected"]:
        print("⚠️  Bias detected — see flagged slices above")
    else:
        print("✅ No bias detected across all slices")
    print("\nRun plot_bias.py to regenerate charts.")


if __name__ == "__main__":
    main()