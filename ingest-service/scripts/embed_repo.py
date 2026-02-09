#!/usr/bin/env python3
"""
Add embeddings to chunked repository
"""
import os
import sys
import argparse
from dotenv import load_dotenv
import config

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.chunking.embedder import ChunkEmbedder

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for chunks')
    parser.add_argument('repo', help='Repository path (owner/repo)')
    parser.add_argument('--force', action='store_true', help='Re-embed existing embeddings')
    parser.add_argument('--batch-size', type=int, default=25, help='Batch size (default: 25)')
    parser.add_argument('--project-id', default=config.getenv('PROJECT_ID'))
    parser.add_argument('--bucket', default=config.getenv('BUCKET_PROCESSED'))
    parser.add_argument('--location', default=config.LOCATION)
    
    args = parser.parse_args()
    
    if not args.project_id or not args.bucket:
        print("Error: PROJECT_ID and BUCKET_PROCESSED must be set")
        sys.exit(1)
    
    # Create embedder
    embedder = ChunkEmbedder(args.project_id, args.bucket, args.location)
    embedder.batch_size = args.batch_size
    
    try:
        stats = embedder.embed_repository(args.repo, args.force)
        
        if stats['failed'] > 0:
            sys.exit(1)
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()