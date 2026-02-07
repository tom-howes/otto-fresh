#!/usr/bin/env python3
"""
Process repository into enriched chunks
"""
import os
import sys
import argparse
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.chunking.enhanced_chunker import EnhancedCodeChunker  # Changed import

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description='Chunk repository with enhanced context')
    parser.add_argument('repo', help='Repository path (owner/repo)')
    parser.add_argument('--chunk-size', type=int, default=150, help='Lines per chunk (default: 150)')
    parser.add_argument('--overlap', type=int, default=10, help='Overlap lines (default: 10)')
    parser.add_argument('--basic', action='store_true', help='Use basic chunker (faster, less context)')
    parser.add_argument('--project-id', default=os.getenv('PROJECT_ID'))
    parser.add_argument('--bucket-raw', default=os.getenv('BUCKET_RAW'))
    parser.add_argument('--bucket-processed', default=os.getenv('BUCKET_PROCESSED'))
    
    args = parser.parse_args()
    
    if not all([args.project_id, args.bucket_raw, args.bucket_processed]):
        print("Error: PROJECT_ID, BUCKET_RAW, and BUCKET_PROCESSED must be set")
        sys.exit(1)
    
    # Choose chunker
    if args.basic:
        from src.chunking.chunker import CodeChunker
        chunker = CodeChunker(args.project_id, args.bucket_raw, args.bucket_processed)
        print("📦 Using BASIC chunker (faster, less context)")
    else:
        chunker = EnhancedCodeChunker(args.project_id, args.bucket_raw, args.bucket_processed)
        print("🚀 Using ENHANCED chunker (rich context extraction)")
    
    chunker.chunk_size = args.chunk_size
    chunker.overlap_lines = args.overlap
    
    try:
        chunks = chunker.process_repository(args.repo)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()