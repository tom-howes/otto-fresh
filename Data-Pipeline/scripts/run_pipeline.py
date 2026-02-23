"""
DVC Pipeline Runner — calls Otto's actual ingest-service classes directly
"""
import os
import sys
import json
import logging
import argparse

# Point to Otto's ingest-service
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), "../../ingest-service"))

os.makedirs("logs", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/pipeline.log")
    ]
)
log = logging.getLogger(__name__)

# Config from env (same vars Otto already uses)
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "otto-pm")
BUCKET_RAW = os.getenv("GCS_BUCKET_RAW", "otto-pm-raw-repos")
BUCKET_PROC = os.getenv("GCS_BUCKET_PROCESSED", "otto-pm-processed-chunks")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("OTTO_REPO", "otto-pm/otto")

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("logs", exist_ok=True)


def ingest():
    from src.ingestion.github_ingester import GitHubIngester
    log.info(f"Ingesting {REPO}...")
    ingester = GitHubIngester(
        project_id=PROJECT_ID,
        bucket_name=BUCKET_RAW,
        github_token=GITHUB_TOKEN
    )
    metadata = ingester.ingest_repository(REPO)
    with open("data/raw/metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    log.info(
        f"Ingested {metadata['total_files']} files @ {metadata['commit_sha'][:8]}")


def chunk():
    from src.chunking.enhanced_chunker import EnhancedCodeChunker

    with open("data/raw/metadata.json") as f:
        metadata = json.load(f)

    repo = metadata["repo_full_name"]        # "otto-pm/otto"
    repo_path = f"repos/{repo}"              # "repos/otto-pm/otto"
    log.info(f"Chunking {repo}...")

    chunker = EnhancedCodeChunker(
        project_id=PROJECT_ID,
        bucket_raw=BUCKET_RAW,
        bucket_processed=BUCKET_PROC
    )

    # Pass repo_path not repo
    chunks = chunker.process_repository(repo_path)

    with open("data/processed/chunks.jsonl", "w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")

    log.info(f"Chunked: {len(chunks)} chunks")


def embed():
    from src.chunking.embedder import ChunkEmbedder
    from google.cloud import storage

    with open("data/raw/metadata.json") as f:
        metadata = json.load(f)

    repo = metadata["repo_full_name"]
    log.info(f"Embedding {repo}...")

    embedder = ChunkEmbedder(
        project_id=PROJECT_ID,
        bucket_processed=BUCKET_PROC,
        location=os.getenv("VERTEX_LOCATION", "us-east1")
    )
    result = embedder.embed_repository(f"repos/{repo}")

    # Pull embedded chunks locally for DVC tracking
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_PROC)
    bucket.blob(f"repos/{repo}/chunks.jsonl").download_to_filename(
        "data/processed/chunks_embedded.jsonl"
    )
    log.info(f"Embedded: {result['newly_embedded']} chunks")


def validate():
    from src.validation import SchemaValidator, AnomalyDetector, BiasDetector
    import json
    from datetime import datetime

    log.info("Validating chunks...")
    chunks = []
    with open("data/processed/chunks_embedded.jsonl") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    schema_report  = SchemaValidator().validate(chunks)
    anomaly_report = AnomalyDetector().detect(chunks, REPO)
    bias_report    = BiasDetector().detect(chunks, REPO)

    print(f"   Schema:  {'✅ PASS' if schema_report['overall_pass'] else '⚠️ FAIL'}")
    print(f"   Anomaly: {'✅ PASS' if anomaly_report['passed'] else '⚠️ FAIL'}")
    print(f"   Bias:    {'✅ None' if not bias_report['bias_detected'] else '⚠️ Detected'}")

    total = len(chunks)
    missing_embedding = sum(1 for c in chunks if not c.get("embedding"))
    missing_content = sum(1 for c in chunks if not c.get("content"))
    missing_language = sum(1 for c in chunks if not c.get("language"))
    empty_content = sum(1 for c in chunks if c.get(
        "content", "").strip() == "")

    report = {
        "timestamp": datetime.now().isoformat(),
        "repo": REPO,
        "total_chunks": total,
        "missing_embedding": missing_embedding,
        "missing_content": missing_content,
        "missing_language": missing_language,
        "empty_content": empty_content,
        "pass": missing_embedding == 0 and missing_content == 0,
    }

    with open("data/processed/validation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    with open("data/processed/schema_validation.json", "w") as f:
        json.dump(schema_report, f, indent=2)

    with open("data/processed/anomaly_detection.json", "w") as f:
        json.dump(anomaly_report, f, indent=2)
    
    with open("data/processed/bias_detection.json", "w") as f:
        json.dump(bias_report, f, indent=2)

    log.info(f"Validation: {'PASS' if report['pass'] else 'FAIL'}")
    log.info(f"  Total chunks:       {total}")
    log.info(f"  Missing embeddings: {missing_embedding}")
    log.info(f"  Missing content:    {missing_content}")

    if not (
        report["pass"] and 
        schema_report["overall_pass"] and 
        not bias_report["bias_detected"] and 
        anomaly_report["passed"]):
        raise ValueError(f"Validation failed see data/processed/*_report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage", choices=["ingest", "chunk", "embed", "validate"])
    args = parser.parse_args()

    stages = {
        "ingest": ingest,
        "chunk": chunk,
        "embed": embed,
        "validate": validate,
    }
    stages[args.stage]()
