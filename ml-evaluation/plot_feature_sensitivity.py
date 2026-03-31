"""
Plot Feature / Input Sensitivity Results
Reads experiments/experiments.jsonl and generates:
  1. Context degradation chart — faithfulness vs top_k (3, 5, 8, 12)
  2. Query rephrasing chart — scores across 3 query phrasings

Usage:
    cd ml-evaluation
    python plot_feature_sensitivity.py

Output:
    charts/sensitivity/feature_context_degradation.png
    charts/sensitivity/feature_query_rephrasing.png
"""
import os
import json
import matplotlib.pyplot as plt
import numpy as np

EXPERIMENTS_LOG = os.path.join(os.path.dirname(__file__), "experiments", "experiments.jsonl")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "charts", "sensitivity")

FAITHFULNESS_THRESHOLD = 0.5
RELEVANCY_THRESHOLD = 0.7
FAITH_COLOR = "#4A90D9"
REL_COLOR = "#7BC67E"

os.makedirs(CHARTS_DIR, exist_ok=True)


def load_runs() -> tuple:
    """Load context degradation (top_k sensitivity) and rephrasing runs."""
    topk_runs = {}
    rephrasing_run = None

    with open(EXPERIMENTS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            run = json.loads(line)
            if run.get("scores", {}).get("faithfulness") is None:
                continue

            if run.get("run_type") == "sensitivity" and run.get("sweep_param") == "top_k":
                val = run["sweep_value"]
                topk_runs[val] = run  # latest wins

            elif run.get("run_type") == "feature_sensitivity_rephrasing":
                rephrasing_run = run  # latest wins

    # Exclude top_k=1 — scores misleadingly high due to constrained context
    topk_runs = {k: v for k, v in topk_runs.items() if k != 1}

    return topk_runs, rephrasing_run


def plot_context_degradation(topk_runs: dict):
    sorted_vals = sorted(topk_runs.keys())
    faith_scores = [topk_runs[v]["scores"]["faithfulness"] for v in sorted_vals]
    rel_scores = [topk_runs[v]["scores"]["answer_relevancy"] for v in sorted_vals]
    labels = [str(v) + (" *" if v == 8 else "") for v in sorted_vals]

    x = np.arange(len(sorted_vals))
    width = 0.35
    n = len(sorted_vals)

    fig, ax = plt.subplots(figsize=(max(8, n * 2), 5))
    bars1 = ax.bar(x - width / 2, faith_scores, width, label="Faithfulness",
                   color=FAITH_COLOR, alpha=0.85, zorder=3)
    bars2 = ax.bar(x + width / 2, rel_scores, width, label="Answer Relevancy",
                   color=REL_COLOR, alpha=0.85, zorder=3)

    ax.axhline(y=FAITHFULNESS_THRESHOLD, color=FAITH_COLOR, linestyle="--",
               linewidth=2.5, zorder=5)
    ax.axhline(y=RELEVANCY_THRESHOLD, color=REL_COLOR, linestyle="--",
               linewidth=2.5, zorder=5)
    ax.fill_betweenx([0, FAITHFULNESS_THRESHOLD], -0.5, n - 0.5,
                     color=FAITH_COLOR, alpha=0.06, zorder=0)
    ax.fill_betweenx([0, RELEVANCY_THRESHOLD], -0.5, n - 0.5,
                     color=REL_COLOR, alpha=0.06, zorder=0)
    ax.text(n - 0.5, FAITHFULNESS_THRESHOLD + 0.02,
            f"Faithfulness threshold ({FAITHFULNESS_THRESHOLD})",
            color=FAITH_COLOR, fontsize=8, ha="right", fontweight="bold")
    ax.text(n - 0.5, RELEVANCY_THRESHOLD + 0.02,
            f"Relevancy threshold ({RELEVANCY_THRESHOLD})",
            color="white", fontsize=8, ha="right", fontweight="bold",
            bbox=dict(facecolor=REL_COLOR, edgecolor="none", pad=2, alpha=0.8))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_xlabel("Top-K Chunks  (* = selected value)", fontsize=10)
    ax.set_ylabel("Score (0-1)")
    ax.set_title("Feature Sensitivity — Context Degradation by Top-K")
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=9)
    ax.bar_label(bars1, labels=[f"{v:.3f}" for v in faith_scores],
                 padding=3, fontsize=9, fontweight="bold")
    ax.bar_label(bars2, labels=[f"{v:.3f}" for v in rel_scores],
                 padding=3, fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "feature_context_degradation.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def plot_query_rephrasing(run: dict):
    queries = run.get("queries", ["Phrasing 1", "Phrasing 2", "Phrasing 3"])
    scores = run["scores"]

    fig, (ax, ax_text) = plt.subplots(2, 1, figsize=(9, 7),
                                       gridspec_kw={"height_ratios": [3, 1]})

    x = np.arange(2)
    width = 0.5
    values = [scores["faithfulness"], scores["answer_relevancy"]]
    colors = [FAITH_COLOR, REL_COLOR]
    thresholds = [FAITHFULNESS_THRESHOLD, RELEVANCY_THRESHOLD]
    metric_labels = ["Faithfulness", "Answer Relevancy"]

    bars = ax.bar(x, values, width, color=colors, alpha=0.85, zorder=3)

    for i, (thresh, color) in enumerate(zip(thresholds, colors)):
        ax.plot([i - 0.4, i + 0.4], [thresh, thresh], color=color,
                linestyle="--", linewidth=2.5, zorder=5)
        ax.text(i + 0.42, thresh + 0.01, f"threshold: {thresh}",
                color=color, fontsize=8, fontweight="bold")
        ax.fill_betweenx([0, thresh], i - 0.4, i + 0.4,
                         color=color, alpha=0.06, zorder=0)

    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, fontsize=10)
    ax.set_ylabel("Score (0-1)")
    ax.set_title("Feature Sensitivity — Query Rephrasing\n(avg RAGAS across 3 phrasings)")
    ax.set_ylim(0, 1.15)
    ax.bar_label(bars, labels=[f"{v:.3f}" for v in values],
                 padding=3, fontsize=11, fontweight="bold")

    ax_text.axis("off")
    for i, q in enumerate(queries):
        ax_text.text(0.01, 0.85 - i * 0.35, f"Phrasing {i+1}: {q}",
                     transform=ax_text.transAxes, fontsize=8,
                     verticalalignment="top", wrap=True)

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "feature_query_rephrasing.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def main():
    print(f"\n{'='*50}")
    print("OTTO — PLOT FEATURE SENSITIVITY RESULTS")
    print(f"{'='*50}")

    topk_runs, rephrasing_run = load_runs()

    if topk_runs:
        print(f"\nFound top_k runs: {sorted(topk_runs.keys())}")
        plot_context_degradation(topk_runs)
    else:
        print("No top_k sensitivity runs found")

    if rephrasing_run:
        print(f"\nFound rephrasing run")
        plot_query_rephrasing(rephrasing_run)
    else:
        print("No rephrasing run found — run run_feature_sensitivity.py first")

    print(f"\nAll charts saved to {CHARTS_DIR}")


if __name__ == "__main__":
    main()