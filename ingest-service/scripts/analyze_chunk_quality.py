# scripts/analyze_chunk_quality.py
#!/usr/bin/env python3
"""
Analyze chunk quality for LLM tasks
"""
import os
import sys
import json
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()


def analyze_chunk_quality(repo_path, sample_size=5):
    """Analyze if chunks have enough context for LLM tasks"""
    
    project_id = os.getenv('PROJECT_ID')
    bucket_name = os.getenv('BUCKET_PROCESSED')
    
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"{repo_path}/chunks.jsonl")
    
    content = blob.download_as_text()
    chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
    
    print(f"{'='*80}")
    print(f"CHUNK QUALITY ANALYSIS: {repo_path}")
    print(f"{'='*80}\n")
    
    # Overall statistics
    print("📊 STATISTICS:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Avg content size: {sum(len(c['content']) for c in chunks) / len(chunks):.0f} chars")
    print(f"  Avg enriched size: {sum(len(c['enriched_content']) for c in chunks) / len(chunks):.0f} chars")
    
    # Check what context is included
    with_imports = sum(1 for c in chunks if c.get('file_imports'))
    with_classes = sum(1 for c in chunks if c.get('file_classes'))
    with_functions = sum(1 for c in chunks if c.get('file_functions'))
    with_embeddings = sum(1 for c in chunks if c.get('embedding'))
    
    print(f"\n📋 CONTEXT COVERAGE:")
    print(f"  With imports: {with_imports}/{len(chunks)} ({with_imports/len(chunks)*100:.1f}%)")
    print(f"  With class info: {with_classes}/{len(chunks)} ({with_classes/len(chunks)*100:.1f}%)")
    print(f"  With function info: {with_functions}/{len(chunks)} ({with_functions/len(chunks)*100:.1f}%)")
    print(f"  With embeddings: {with_embeddings}/{len(chunks)} ({with_embeddings/len(chunks)*100:.1f}%)")
    
    # Analyze chunk types
    chunk_types = {}
    for chunk in chunks:
        chunk_type = chunk.get('chunk_type', 'unknown')
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
    
    print(f"\n🏷️  CHUNK TYPES:")
    for ctype, count in sorted(chunk_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ctype}: {count} ({count/len(chunks)*100:.1f}%)")
    
    # Sample chunks for quality review
    print(f"\n{'='*80}")
    print(f"SAMPLE CHUNKS (showing {sample_size}):")
    print(f"{'='*80}\n")
    
    for i, chunk in enumerate(chunks[:sample_size], 1):
        print(f"{'─'*80}")
        print(f"CHUNK {i}: {chunk['file_path']}")
        print(f"{'─'*80}")
        print(f"Type: {chunk['chunk_type']}")
        print(f"Name: {chunk['chunk_name']}")
        print(f"Lines: {chunk['start_line']}-{chunk['end_line']} ({chunk['num_lines']} lines)")
        print(f"Language: {chunk['language']}")
        print(f"\nContext Available:")
        print(f"  Imports: {', '.join(chunk.get('file_imports', [])[:3]) or 'None'}")
        print(f"  Classes: {', '.join(chunk.get('file_classes', [])) or 'None'}")
        print(f"  Functions: {', '.join(chunk.get('file_functions', [])[:5]) or 'None'}")
        
        print(f"\nEnriched Content Preview (first 500 chars):")
        print("─" * 80)
        preview = chunk['enriched_content'][:500]
        print(preview)
        if len(chunk['enriched_content']) > 500:
            print(f"\n... (truncated, total {len(chunk['enriched_content'])} chars)")
        print()
    
    # Assess quality for specific tasks
    print(f"\n{'='*80}")
    print("TASK READINESS ASSESSMENT:")
    print(f"{'='*80}\n")
    
    assess_documentation_readiness(chunks)
    assess_code_completion_readiness(chunks)
    assess_qa_readiness(chunks)
    
    return chunks


def assess_documentation_readiness(chunks):
    """Check if chunks are good for generating documentation"""
    print("📝 DOCUMENTATION GENERATION:")
    
    # For documentation, we need:
    # 1. Function/class definitions with their full context
    # 2. Related imports to understand dependencies
    # 3. Surrounding code for understanding purpose
    
    semantic_chunks = [c for c in chunks if c['chunk_type'] in [
        'function_definition', 'class_definition', 'method_definition'
    ]]
    
    chunks_with_context = [c for c in chunks if c.get('file_imports') and len(c['content']) > 100]
    
    print(f"  ✓ Semantic chunks (functions/classes): {len(semantic_chunks)}/{len(chunks)} "
          f"({len(semantic_chunks)/len(chunks)*100:.1f}%)")
    print(f"  ✓ Chunks with import context: {chunks_with_context}/{len(chunks)} "
          f"({len(chunks_with_context)/len(chunks)*100:.1f}%)")
    
    if len(semantic_chunks) > len(chunks) * 0.3:
        print("  ✅ GOOD: High semantic chunk ratio - good for documentation")
    else:
        print("  ⚠️  MODERATE: Lower semantic chunks - may need improvement")
    
    # Check average context size
    avg_enriched = sum(len(c['enriched_content']) for c in chunks) / len(chunks)
    if avg_enriched > 1500:
        print(f"  ✅ GOOD: Rich context ({avg_enriched:.0f} chars avg)")
    else:
        print(f"  ⚠️  MODERATE: Context could be richer ({avg_enriched:.0f} chars avg)")
    
    print()


def assess_code_completion_readiness(chunks):
    """Check if chunks are good for code completion"""
    print("💻 CODE COMPLETION:")
    
    # For code completion, we need:
    # 1. Full function signatures and bodies
    # 2. Import statements (to understand available libraries)
    # 3. Variable and class definitions in scope
    # 4. Smaller, more focused chunks
    
    small_chunks = [c for c in chunks if c['num_lines'] < 100]
    with_imports = [c for c in chunks if c.get('file_imports')]
    
    print(f"  ✓ Focused chunks (<100 lines): {len(small_chunks)}/{len(chunks)} "
          f"({len(small_chunks)/len(chunks)*100:.1f}%)")
    print(f"  ✓ Chunks with import context: {len(with_imports)}/{len(chunks)} "
          f"({len(with_imports)/len(chunks)*100:.1f}%)")
    
    if len(with_imports) > len(chunks) * 0.7:
        print("  ✅ GOOD: Most chunks have import context")
    else:
        print("  ⚠️  NEEDS IMPROVEMENT: Add more import/dependency context")
    
    # Check if we have function/class names
    with_functions = [c for c in chunks if c.get('file_functions')]
    if len(with_functions) > len(chunks) * 0.5:
        print("  ✅ GOOD: Function context available for intelligent completion")
    else:
        print("  ⚠️  NEEDS IMPROVEMENT: Add more function/class context")
    
    print()


def assess_qa_readiness(chunks):
    """Check if chunks are good for Q&A"""
    print("❓ CODE Q&A / SEARCH:")
    
    # For Q&A, we need:
    # 1. Self-contained chunks with full context
    # 2. Repository-level context
    # 3. File-level context
    # 4. Embeddings for semantic search
    
    with_embeddings = [c for c in chunks if c.get('embedding')]
    self_contained = [c for c in chunks if len(c['enriched_content']) > 1000]
    
    print(f"  ✓ With embeddings: {len(with_embeddings)}/{len(chunks)} "
          f"({len(with_embeddings)/len(chunks)*100:.1f}%)")
    print(f"  ✓ Self-contained chunks (>1000 chars): {len(self_contained)}/{len(chunks)} "
          f"({len(self_contained)/len(chunks)*100:.1f}%)")
    
    if len(with_embeddings) == len(chunks):
        print("  ✅ EXCELLENT: All chunks have embeddings for semantic search")
    elif len(with_embeddings) > 0:
        print("  ⚠️  PARTIAL: Some chunks missing embeddings")
    else:
        print("  ❌ NEEDS EMBEDDINGS: Run embed_repo.py to enable semantic search")
    
    if len(self_contained) > len(chunks) * 0.6:
        print("  ✅ GOOD: Most chunks are self-contained with rich context")
    else:
        print("  ⚠️  MODERATE: Consider larger chunks or more context")
    
    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_chunk_quality.py <repo_path>")
        sys.exit(1)
    
    analyze_chunk_quality(sys.argv[1])