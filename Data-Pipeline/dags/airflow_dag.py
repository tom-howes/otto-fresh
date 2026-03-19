
"""
Otto Data Pipeline — Airflow DAG

Orchestrates the 4-stage pipeline (ingest → chunk → embed → validate)
using the same run_pipeline.py script that DVC uses. Airflow handles
scheduling and orchestration; DVC continues to handle data versioning.

Each task calls `python scripts/run_pipeline.py <stage>` via
BashOperator, so there is zero code duplication between the
Airflow and DVC pipelines.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
import os

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Base directory for the Data-Pipeline (adjust if needed)
PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Environment variables passed to every task — same vars used by DVC
ENV_VARS = " ".join([
    'GITHUB_TOKEN="${GITHUB_TOKEN}"',
    'GCP_PROJECT_ID="${GCP_PROJECT_ID}"',
    'GCS_BUCKET_RAW="${GCS_BUCKET_RAW}"',
    'GCS_BUCKET_PROCESSED="${GCS_BUCKET_PROCESSED}"',
    'VERTEX_LOCATION="${VERTEX_LOCATION}"',
    'OTTO_REPO="otto-pm/otto"',
    'GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS}"',
])

default_args = {
    "owner": "otto",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

# ---------------------------------------------------------------------------
# DAG Definition
# ---------------------------------------------------------------------------

with DAG(
    dag_id="airflow_dag",
    default_args=default_args,
    description="Otto: Ingest → Chunk → Embed → Validate",
    # Schedule disabled — triggered manually or via API
    schedule_interval=None,
    start_date=datetime(2026, 2, 1),
    catchup=False,
    tags=["otto", "pipeline", "mlops"],
) as dag:

    def make_task(stage, task_id=None):
        """Create a BashOperator that runs a pipeline stage."""
        return BashOperator(
            task_id=task_id or stage,
            bash_command=f"cd {PIPELINE_DIR} && {ENV_VARS} python scripts/run_pipeline.py {stage}",
        )

    # --- Pipeline stages ---
    ingest = make_task("ingest")
    chunk = make_task("chunk")
    embed = make_task("embed")
    validate = make_task("validate")

    # --- DAG dependency chain ---
    ingest >> chunk >> embed >> validate
