#!/usr/bin/env python3
"""
CLI tool to ingest GitHub repositories
"""
import os
import sys
import argparse
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.github_ingester import GitHubIngester

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description='Ingest GitHub repository')
    parser.add_argument('repo', help='GitHub repo (owner/repo or full URL)')
    parser.add_argument('--branch', help='Specific branch (optional)')
    parser.add_argument('--project-id', default=os.getenv('PROJECT_ID'))
    parser.add_argument('--bucket', default=os.getenv('BUCKET_RAW'))
    parser.add_argument('--token', default=os.getenv('GITHUB_TOKEN'))
    
    args = parser.parse_args()
    
    if not args.project_id or not args.bucket:
        print("Error: PROJECT_ID and BUCKET_RAW must be set")
        sys.exit(1)
    
    ingester = GitHubIngester(args.project_id, args.bucket, args.token)
    
    try:
        metadata = ingester.ingest_repository(args.repo, args.branch)
        print(f"\n✅ Ingestion complete!")
        print(f"Repository: {metadata['repo']}")
        print(f"Files: {metadata['total_files']}")
        print(f"To process: python scripts/process_repo.py {metadata['repo']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()