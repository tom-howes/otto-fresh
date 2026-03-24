"""
Plot Results
Reads experiments/experiments.jsonl and generates bar charts.

Usage:
    cd ml-evaluation
    python plot_results.py

Output:
    charts/scores_by_run.png
    charts/scores_by_prompt_version.png
    charts/latest_run_summary.png
"""
import os
import json
import matplotlib.pyplot as plt
import numpy as np

EXPERIMENTS_LOG = os.path.join(os.path.dirname(__file__), "experiments", "experiments.jsonl")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "charts")

FAITHFULNESS_THRESHOLD = 0.5
RELEVANCY_THRESHOLD = 0.7

FAITH_COLOR = "#4A90D9"
REL_COLOR = "#7BC67E"

os.makedirs(CHARTS_DIR, exist_ok=True)


def load_runs() -> list:
    runs = []
    with open(EXPERIMENTS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            run = json.loads(line)
            if run.get("scores", {}).get("faithfulness") is not None:
                runs.append(run)
    print(f"✓ Loaded {len(runs)} runs")
    return runs


def add_thresholds(ax, n_bars):
    """Add clearly visible threshold lines with labels and shading."""
    ax.axhline(y=FAITHFULNESS_THRESHOLD, color=FAITH_COLOR, linestyle="--",
               linewidth=2.5, zorder=5)
    ax.axhline(y=RELEVANCY_THRESHOLD, color=REL_COLOR, linestyle="--",
               linewidth=2.5, zorder=5)
    ax.fill_betweenx([0, FAITHFULNESS_THRESHOLD], -0.5, n_bars - 0.5,
                     color=FAITH_COLOR, alpha=0.06, zorder=0)
    ax.fill_betweenx([0, RELEVANCY_THRESHOLD], -0.5, n_bars - 0.5,
                     color=REL_COLOR, alpha=0.06, zorder=0)
    ax.text(n_bars - 0.5, FAITHFULNESS_THRESHOLD + 0.02,
            f"Faithfulness threshold ({FAITHFULNESS_THRESHOLD})",
            color=FAITH_COLOR, fontsize=8, ha="right", fontweight="bold")
    ax.text(n_bars - 0.5, RELEVANCY_THRESHOLD + 0.02,
            f"Relevancy threshold ({RELEVANCY_THRESHOLD})",
            color="white", fontsize=8, ha="right", fontweight="bold",
            bbox=dict(facecolor=REL_COLOR, edgecolor="none", pad=2, alpha=0.8))


def plot_scores_by_run(runs: list):
    """Bar chart showing average faithfulness and relevancy across all runs."""
    faith_avg = round(np.mean([r["scores"]["faithfulness"] for r in runs]), 3)
    rel_avg = round(np.mean([r["scores"]["answer_relevancy"] for r in runs]), 3)

    metrics = ["Faithfulness", "Answer Relevancy"]
    values = [faith_avg, rel_avg]
    colors = [FAITH_COLOR, REL_COLOR]
    thresholds = [FAITHFULNESS_THRESHOLD, RELEVANCY_THRESHOLD]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(metrics, values, color=colors, alpha=0.85, zorder=3)

    for i, (thresh, color) in enumerate(zip(thresholds, colors)):
        ax.plot([i - 0.4, i + 0.4], [thresh, thresh], color=color,
                linestyle="--", linewidth=2.5, zorder=5)
        ax.text(i + 0.42, thresh + 0.01, f"threshold: {thresh}",
                color=color, fontsize=8, fontweight="bold")
        ax.fill_betweenx([0, thresh], i - 0.4, i + 0.4,
                         color=color, alpha=0.06, zorder=0)

    ax.set_ylabel("Score (0-1)")
    ax.set_title("RAGAS Validation Scores — Average Across All Runs")
    ax.set_ylim(0, 1.0)
    ax.bar_label(bars, labels=[f"{v:.3f}" for v in values],
                 padding=6, fontsize=10, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "scores_by_run.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✓ Saved: {path}")





def plot_latest_run_summary(runs: list):
    """Bar chart of the most recent run's scores vs thresholds."""
    latest = runs[-1]
    scores = latest["scores"]

    metrics = ["Faithfulness", "Answer Relevancy"]
    values = [scores["faithfulness"], scores["answer_relevancy"]]
    thresholds = [FAITHFULNESS_THRESHOLD, RELEVANCY_THRESHOLD]
    colors = [FAITH_COLOR, REL_COLOR]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(metrics, values, color=colors, alpha=0.85, zorder=3)

    for i, (thresh, color) in enumerate(zip(thresholds, colors)):
        ax.plot([i - 0.4, i + 0.4], [thresh, thresh], color=color,
                linestyle="--", linewidth=2.5, zorder=5)
        ax.text(i + 0.42, thresh + 0.01, f"threshold: {thresh}",
                color=color, fontsize=8, fontweight="bold")
        ax.fill_betweenx([0, thresh], i - 0.4, i + 0.4,
                         color=color, alpha=0.06, zorder=0)

    ax.set_ylabel("Score (0-1)")
    ax.set_title(f"Latest Validation Run — {latest['timestamp'][:10]}")
    ax.set_ylim(0, 1.15)
    ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=11, fontweight="bold")

    passed = latest.get("passed", False)
    status = "✅ PASSED" if passed else "❌ FAILED"
    ax.text(0.5, 1.08, status, transform=ax.transAxes,
            ha="center", fontsize=12, fontweight="bold",
            color="green" if passed else "red")

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "latest_run_summary.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✓ Saved: {path}")


def main():
    print(f"\n{'='*50}")
    print("📊 OTTO — PLOT RESULTS")
    print(f"{'='*50}")

    runs = load_runs()

    if not runs:
        print("❌ No runs found in experiments.jsonl")
        return

    plot_scores_by_run(runs)
    plot_latest_run_summary(runs)

    print(f"\n✅ All charts saved to {CHARTS_DIR}")
    print("   Include these in your ML development document.")


if __name__ == "__main__":
    main()