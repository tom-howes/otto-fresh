"""
Generate a Gantt chart from DVC pipeline logs.

Parses stage-level timing from Data-Pipeline/logs/pipeline.log
and renders a terminal-based Gantt chart showing per-stage
duration and percentage of total runtime. Used to identify
pipeline bottlenecks (Section 2.9 of the data pipeline report).

The log file may contain multiple pipeline runs. By default
the most recent run is displayed. Use --run N to select a
specific run or --list to see all available runs.

Usage:
    python scripts/gantt.py             # uses latest run
    python scripts/gantt.py --run 1     # uses first run
    python scripts/gantt.py --list      # lists all runs

Requirements:
    - Python 3.11+ (standard library only, no external dependencies)
    - Log file at Data-Pipeline/logs/pipeline.log with timestamped
      entries in the format: YYYY-MM-DD HH:MM:SS,mmm [INFO] <message>
"""

import re
import os
import sys
from datetime import datetime

# ---------------------------------
# Configuration
# ---------------------------------

# Resolve paths relative to this script so it works from any directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_FILE = os.path.join(PIPELINE_DIR, "logs", "pipeline.log")

# Each pipeline stage is identified by a start and end regex pattern
# matched against log messages. Order here determines display order.
STAGE_PATTERNS = {
    "Ingest":   (r"Ingesting", r"Ingested"),
    "Chunk":    (r"Chunking", r"Chunked"),
    "Embed":    (r"Embedding", r"Embedded"),
    "Validate": (r"Validating", r"Validation"),
}

# Gantt chart display settings
BAR_WIDTH = 40  # character width of each bar
BAR_CHARS = ["█", "▓", "▒", "░"]  # rotating fill characters per stage

# ---------------------------------
# Parse log file
# ---------------------------------

with open(LOG_FILE, "r") as f:
    lines = f.readlines()

# Split log into separate runs. Each run starts with an "Ingesting"
# message, so we use that as a delimiter to group lines into per-run
# lists.
runs = []
current = []
for line in lines:
    if re.search(r"Ingesting", line):
        if current:
            runs.append(current)
        current = [line]
    else:
        current.append(line)
if current:
    runs.append(current)

# ---------------------------------
# CLI argument handling
# ---------------------------------

# --list: print all available runs with timestamps and exit
if "--list" in sys.argv:
    print(f"\nFound {len(runs)} pipeline run(s):\n")
    for i, run in enumerate(runs, 1):
        ts = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", run[0])
        print(f"  Run {i}: {ts.group(1) if ts else 'unknown'}")
    print(f"\nUsage: python scripts/gantt.py --run <number>")
    sys.exit(0)

# --run N: select a specific run (1-indexed). Default: -1 (latest run)
run_idx = -1
if "--run" in sys.argv:
    idx = sys.argv.index("--run") + 1
    if idx < len(sys.argv):
        run_idx = int(sys.argv[idx]) - 1  # convert to 0-indexed

if run_idx >= len(runs) or abs(run_idx) > len(runs):
    print(f"Error: only {len(runs)} run(s) found. Use --list to see them.")
    sys.exit(1)

selected = runs[run_idx]

# ---------------------------------
# Stage timing extraction
# ---------------------------------


def find_timestamp(lines, pattern):
    """Search lines for a regex pattern and return the timestamp of the
    first matching line, or None if no match is found.

    Args:
        lines: List of log lines to search.
        pattern: Regex pattern to match against each line.

    Returns:
        datetime object of the matching line's timestamp, or None.
    """
    for line in lines:
        if re.search(pattern, line):
            match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
            if match:
                return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    return None


# Build list of stages with their start time,
# end time, and duration
stages = []
for name, (start_pat, end_pat) in STAGE_PATTERNS.items():
    start = find_timestamp(selected, start_pat)
    end = find_timestamp(selected, end_pat)
    if start and end:
        duration = (end - start).total_seconds()
        stages.append({
            "name": name,
            "start": start,
            "end": end,
            "duration": duration
        })

total = sum(s["duration"] for s in stages)

# ---------------------------------
# Render terminal Gantt chart
# ---------------------------------

print(f"\n{'=' * 65}")
print(f"  DVC Pipeline Gantt Chart — {stages[0]['start'].strftime('%Y-%m-%d %H:%M')}")
print(f"  Total: {total:.0f}s")
print(f"{'=' * 65}")

for i, s in enumerate(stages):
    pct = (s["duration"] / total) * 100
    filled = int((s["duration"] / total) * BAR_WIDTH)
    bar = BAR_CHARS[i % len(BAR_CHARS)] * filled + "·" * (BAR_WIDTH - filled)
    print(f"  {s['name']:10s} |{bar}| {s['duration']:>5.0f}s ({pct:4.1f}%)")

print(f"{'=' * 65}")

# Identify and display the bottleneck stage
bottleneck = max(stages, key=lambda s: s["duration"])
bottleneck_pct = bottleneck["duration"] / total * 100
print(f"\n  Bottleneck: {bottleneck['name']}"
      f" ({bottleneck['duration']:.0f}s, {bottleneck_pct:.0f}% of total)")
print()
