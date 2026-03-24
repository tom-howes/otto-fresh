"""
Plot Sensitivity Results
Reads experiments/experiments.jsonl and generates temperature and top-k
sensitivity bar charts.

Usage:
    cd ml-evaluation
    python plot_sensitivity.py

Output:
    charts/sensitivity/sensitivity_temperature.png
    charts/sensitivity/sensitivity_topk.png
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


def load_sensitivity_runs() -> dict:
    """Load sensitivity runs grouped by sweep_param, latest value per sweep_value wins."""
    runs = {}
    with open(EXPERIMENTS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            run = json.loads(line)
            if run.get("run_type") != "sensitivity":
                continue
            if run.get("scores", {}).get("faithfulness") is None:
                continue
            param = run["sweep_param"]
            val = run["sweep_value"]
            runs.setdefault(param, {})[val] = run
    return runs


def plot_sweep(param_name: str, runs_by_value: dict, default_val, filename: str):
    # Sort by sweep value
    sorted_vals = sorted(runs_by_value.keys())
    faith_scores = [runs_by_value[v]["scores"]["faithfulness"] for v in sorted_vals]
    rel_scores = [runs_by_value[v]["scores"]["answer_relevancy"] for v in sorted_vals]
    labels = [str(v) + (" ★" if v == default_val else "") for v in sorted_vals]

    x = np.arange(len(sorted_vals))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(x - width / 2, faith_scores, width, label="Faithfulness",
                   color=FAITH_COLOR, alpha=0.85, zorder=3)
    bars2 = ax.bar(x + width / 2, rel_scores, width, label="Answer Relevancy",
                   color=REL_COLOR, alpha=0.85, zorder=3)

    # Threshold lines — consistent with plot_val.py and plot_bias.py
    ax.axhline(y=FAITHFULNESS_THRESHOLD, color=FAITH_COLOR, linestyle="--",
               linewidth=2.5, zorder=5)
    ax.axhline(y=RELEVANCY_THRESHOLD, color=REL_COLOR, linestyle="--",
               linewidth=2.5, zorder=5)
    ax.fill_betweenx([0, FAITHFULNESS_THRESHOLD], -0.5, len(sorted_vals) - 0.5,
                     color=FAITH_COLOR, alpha=0.06, zorder=0)
    ax.fill_betweenx([0, RELEVANCY_THRESHOLD], -0.5, len(sorted_vals) - 0.5,
                     color=REL_COLOR, alpha=0.06, zorder=0)
    ax.text(len(sorted_vals) - 0.5, FAITHFULNESS_THRESHOLD + 0.02,
            f"Faithfulness threshold ({FAITHFULNESS_THRESHOLD})",
            color=FAITH_COLOR, fontsize=8, ha="right", fontweight="bold")
    ax.text(len(sorted_vals) - 0.5, RELEVANCY_THRESHOLD + 0.02,
            f"Relevancy threshold ({RELEVANCY_THRESHOLD})",
            color="white", fontsize=8, ha="right", fontweight="bold",
            bbox=dict(facecolor=REL_COLOR, edgecolor="none", pad=2, alpha=0.8))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_xlabel(f"{param_name}  (★ = selected value)", fontsize=10)
    ax.set_ylabel("Score (0-1)")
    ax.set_title(f"RAGAS Sensitivity Analysis — {param_name}")
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=9)
    ax.bar_label(bars1, labels=[f"{v:.3f}" for v in faith_scores],
                 padding=3, fontsize=9, fontweight="bold")
    ax.bar_label(bars2, labels=[f"{v:.3f}" for v in rel_scores],
                 padding=3, fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✓ Saved: {path}")


def main():
    print(f"\n{'='*50}")
    print("📊 OTTO — PLOT SENSITIVITY RESULTS")
    print(f"{'='*50}")

    runs = load_sensitivity_runs()

    if not runs:
        print("❌ No sensitivity runs found in experiments.jsonl")
        return

    if "temperature" in runs:
        plot_sweep("Temperature", runs["temperature"], default_val=0.2,
                   filename="sensitivity_temperature.png")
    else:
        print("⚠️  No temperature sweep results found")

    if "top_k" in runs:
        plot_sweep("Top-K Chunks", runs["top_k"], default_val=8,
                   filename="sensitivity_topk.png")
    else:
        print("⚠️  No top-k sweep results found")

    print(f"\n✅ All sensitivity charts saved to {CHARTS_DIR}")


if __name__ == "__main__":
    main()