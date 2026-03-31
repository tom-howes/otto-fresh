"""
Plot Bias Results
Reads reports/bias_report.json and generates per-dimension bar charts.

Usage:
    cd ml-evaluation
    python plot_bias.py

Output:
    charts/bias/bias_language.png
    charts/bias/bias_repo_section.png
    charts/bias/bias_chunk_size.png
"""
import os
import json
import matplotlib.pyplot as plt
import numpy as np

REPORT_PATH = os.path.join(os.path.dirname(__file__), "reports", "bias_report.json")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "charts", "bias")

FAITHFULNESS_THRESHOLD = 0.5
RELEVANCY_THRESHOLD = 0.7
FAITH_COLOR = "#4A90D9"
REL_COLOR = "#7BC67E"
FLAG_COLOR = "#E05C5C"

os.makedirs(CHARTS_DIR, exist_ok=True)


def plot_slice_chart(dimension: str, slice_names: list, faith_scores: list,
                     rel_scores: list, flagged: set, filename: str):
    x = np.arange(len(slice_names))
    width = 0.35
    n_bars = len(slice_names)

    bar_colors_f = [FLAG_COLOR if n in flagged else FAITH_COLOR for n in slice_names]
    bar_colors_r = [FLAG_COLOR if n in flagged else REL_COLOR for n in slice_names]

    fig, ax = plt.subplots(figsize=(max(8, n_bars * 2), 5))
    bars1 = ax.bar(x - width / 2, faith_scores, width, label="Faithfulness",
                   color=bar_colors_f, alpha=0.85, zorder=3)
    bars2 = ax.bar(x + width / 2, rel_scores, width, label="Answer Relevancy",
                   color=bar_colors_r, alpha=0.85, zorder=3)

    # Threshold lines with shading — matching plot_val.py style
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

    ax.set_xticks(x)
    ax.set_xticklabels(slice_names, fontsize=10)
    ax.set_xlabel(f"{dimension} slice", fontsize=10)
    ax.set_ylabel("Score (0-1)")
    ax.set_title(f"RAGAS Bias Evaluation — by {dimension}")
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
    print(f"Saved: {path}")


def main():
    print(f"\n{'='*50}")
    print("OTTO — PLOT BIAS RESULTS")
    print(f"{'='*50}")

    with open(REPORT_PATH, "r") as f:
        report = json.load(f)

    for dimension, data in report["dimensions"].items():
        slices = data["slices"]
        flagged = set(data.get("flagged_slices", []))

        names = list(slices.keys())
        faith_vals = [slices[n]["faithfulness"] or 0.0 for n in names]
        rel_vals = [slices[n]["answer_relevancy"] or 0.0 for n in names]

        plot_slice_chart(
            dimension, names, faith_vals, rel_vals,
            flagged=flagged,
            filename=f"bias_{dimension.replace('-', '_').lower()}.png",
        )

    print(f"\nAll bias charts saved to {CHARTS_DIR}")


if __name__ == "__main__":
    main()