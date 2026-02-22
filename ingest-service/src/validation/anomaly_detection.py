"""
Anomaly Detection
Detects: missing values, outliers, duplicates, wrong dimensions
Alerts via: Slack webhook (optional)
"""
import json
import logging
import statistics
import urllib.request
import os
from datetime import datetime
from typing import List, Dict

log = logging.getLogger(__name__)

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_alert(message: str):
    if not SLACK_WEBHOOK:
        log.warning("SLACK_WEBHOOK_URL not set — skipping Slack alert")
        return
    try:
        payload = json.dumps({
            "text": f":warning: *Otto Pipeline Alert*\n{message}"
        }).encode()
        req = urllib.request.Request(
            SLACK_WEBHOOK,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
        log.info("Slack alert sent")
    except Exception as e:
        log.error(f"Slack alert failed: {e}")


class AnomalyDetector:

    def detect(self, chunks: List[Dict], repo: str = "") -> Dict:
        anomalies = []
        warnings = []

        if not chunks:
            anomalies.append("CRITICAL: No chunks found in dataset")
            return {
                "timestamp": datetime.now().isoformat(),
                "repo": repo,
                "anomalies": anomalies,
                "warnings": warnings,
                "passed": False
            }

        # ── Missing value checks ──────────────────────────────────
        missing_content = sum(
            1 for c in chunks if not c.get("content", "").strip()
        )
        if missing_content:
            anomalies.append(
                f"MISSING CONTENT: {missing_content} chunks have empty content"
            )

        missing_embedding = sum(1 for c in chunks if not c.get("embedding"))
        if missing_embedding:
            anomalies.append(
                f"MISSING EMBEDDING: {missing_embedding} chunks have no embedding"
            )

        missing_language = sum(1 for c in chunks if not c.get("language"))
        if missing_language:
            anomalies.append(
                f"MISSING LANGUAGE: {missing_language} chunks have no language tag"
            )

        missing_file = sum(1 for c in chunks if not c.get("file_path"))
        if missing_file:
            anomalies.append(
                f"MISSING FILE PATH: {missing_file} chunks have no file path"
            )

        # ── Outlier detection ─────────────────────────────────────
        sizes = [len(c.get("content", "")) for c in chunks]
        if len(sizes) > 1:
            mean = statistics.mean(sizes)
            stdev = statistics.stdev(sizes)
            outliers = sum(
                1 for s in sizes
                if stdev > 0 and abs(s - mean) > 3 * stdev
            )
            if outliers:
                warnings.append(
                    f"OUTLIER CHUNKS: {outliers} chunks are size outliers (>3σ)"
                )

        tiny = sum(1 for s in sizes if s < 10)
        if tiny:
            warnings.append(f"TINY CHUNKS: {tiny} chunks < 10 characters")

        huge = sum(1 for s in sizes if s > 10000)
        if huge:
            warnings.append(f"HUGE CHUNKS: {huge} chunks > 10,000 characters")

        # ── Embedding dimension check ─────────────────────────────
        wrong_dim = sum(
            1 for c in chunks
            if c.get("embedding") and len(c["embedding"]) != 768
        )
        if wrong_dim:
            anomalies.append(
                f"WRONG EMBEDDING DIM: {wrong_dim} embeddings are not 768-dim"
            )

        # ── Duplicate detection ───────────────────────────────────
        contents = [c.get("content", "") for c in chunks]
        duplicates = len(contents) - len(set(contents))
        if duplicates > 0:
            warnings.append(f"DUPLICATES: {duplicates} duplicate chunks")

        # ── Language distribution ─────────────────────────────────
        languages = {}
        for c in chunks:
            lang = c.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1

        unknown_pct = (languages.get("unknown", 0) / len(chunks)) * 100
        if unknown_pct > 20:
            warnings.append(
                f"HIGH UNKNOWN LANGUAGE: {unknown_pct:.1f}% chunks undetected"
            )

        report = {
            "timestamp": datetime.now().isoformat(),
            "repo": repo,
            "total_chunks": len(chunks),
            "anomalies": anomalies,
            "warnings": warnings,
            "passed": len(anomalies) == 0,
            "summary": {
                "missing_content": missing_content,
                "missing_embedding": missing_embedding,
                "missing_language": missing_language,
                "duplicates": duplicates,
                "language_distribution": languages,
            }
        }

        # Send alert if anomalies found
        if anomalies:
            alert_msg = f"Repo: {repo}\n" + "\n".join(anomalies)
            send_slack_alert(alert_msg)

        return report