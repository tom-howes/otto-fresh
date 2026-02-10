"""
Pure chunking module - No embeddings, just smart code chunking
"""
import hashlib
import json
import re
import time
from typing import List, Dict
from google.cloud import storage


class CodeChunker:
    """
    Smart code chunker with context enrichment
    Handles: Ingestion → Chunking → Context Building → Storage
    """
    
    def __init__(self, project_id: str, bucket_raw: str, bucket_processed: str):
        """
        Initialize the chunker
        
        Args:
            project_id: GCP project ID
            bucket_raw: Bucket with raw ingested files
            bucket_processed: Bucket for processed chunks
        """
        self.project_id = project_id
        self.bucket_raw = bucket_raw
        self.bucket_processed = bucket_processed
        
        self.storage_client = storage.Client(project=project_id)
        self.parsers = {}
        
        # Chunking settings
        self.chunk_size = 150  # lines per chunk
        self.overlap_lines = 10  # overlap between chunks
        
        self._load_parsers()
    
    def _load_parsers(self):
        """Load tree-sitter parsers for semantic analysis"""
        try:
            from tree_sitter_languages import get_parser
            languages = ['python', 'javascript', 'typescript', 'java', 'go', 'rust']
            loaded = 0
            for lang in languages:
                try:
                    self.parsers[lang] = get_parser(lang)
                    loaded += 1
                except Exception:
                    pass
            if loaded > 0:
                print(f"✓ Loaded {loaded} language parsers")
        except ImportError:
            print("⚠️  tree-sitter not available, using line-based chunking")
    
    def process_repository(self, repo_path: str) -> List[Dict]:
        """
        Process a repository into context-rich chunks
        
        Args:
            repo_path: Repository path (owner/repo)
            
        Returns:
            List of chunk dictionaries (without embeddings)
        """
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"🔧 CHUNKING: {repo_path}")
        print(f"{'='*60}")
        
        # Load metadata
        metadata = self._load_metadata(repo_path)
        total_files = len(metadata['files'])
        print(f"📁 Files to process: {total_files}")
        print(f"📏 Chunk size: {self.chunk_size} lines with {self.overlap_lines} line overlap")
        
        # Build repository context
        repo_context = self._build_repo_context(metadata)
        print(f"📊 Primary language: {repo_context['primary_language']}")
        
        # Process files
        all_chunks = []
        processed_files = 0
        
        for file_meta in metadata['files']:
            try:
                # Read file
                content = self._read_file(file_meta['blob_path'])
                
                # Extract file-level context
                file_context = self._extract_file_context(content, file_meta['language'])
                
                # Chunk file
                chunks = self._chunk_file(
                    file_meta['path'],
                    content,
                    file_meta['language'],
                    metadata,
                    file_context,
                    repo_context
                )
                
                all_chunks.extend(chunks)
                processed_files += 1
                
                # Progress
                if processed_files % 10 == 0 or processed_files == total_files:
                    elapsed = time.time() - start_time
                    rate = processed_files / elapsed if elapsed > 0 else 0
                    print(f"✓ {processed_files}/{total_files} files "
                          f"({len(all_chunks)} chunks, {rate:.1f} files/sec)")
                
            except Exception as e:
                print(f"⚠️  Error processing {file_meta['path']}: {e}")
                continue
        
        # Save chunks
        self._save_chunks(repo_path, all_chunks)
        
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ CHUNKING COMPLETE")
        print(f"{'='*60}")
        print(f"Total chunks: {len(all_chunks)}")
        print(f"Time: {elapsed:.1f}s ({len(all_chunks)/elapsed:.1f} chunks/sec)")
        print(f"Avg chunk size: {sum(len(c['content']) for c in all_chunks) / len(all_chunks):.0f} chars")
        print(f"Storage: gs://{self.bucket_processed}/{repo_path}/chunks.jsonl")
        
        return all_chunks
    
    def _build_repo_context(self, metadata: Dict) -> Dict:
        """Build high-level repository context"""
        languages = {}
        directories = set()
        
        for file in metadata['files']:
            lang = file.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1
            
            # Extract directory
            path_parts = file['path'].split('/')
            if len(path_parts) > 1:
                directories.add('/'.join(path_parts[:-1]))
        
        return {
            'repo_name': metadata['repo'],
            'description': metadata.get('repo_info', {}).get('description', ''),
            'primary_language': metadata.get('repo_info', {}).get('language', 'Unknown'),
            'total_files': metadata['total_files'],
            'languages': languages,
            'directories': sorted(list(directories))[:20]  # Top 20
        }
    
    def _extract_file_context(self, content: str, language: str) -> Dict:
        """Extract file-level context (imports, classes, functions)"""
        context = {
            'imports': [],
            'classes': [],
            'functions': [],
            'constants': [],
            'docstring': None
        }
        
        lines = content.split('\n')[:100]  # Analyze first 100 lines
        
        if language == 'python':
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('import ', 'from ')):
                    match = re.search(r'(?:from|import)\s+([\w.]+)', line)
                    if match and len(context['imports']) < 15:
                        context['imports'].append(match.group(1))
                elif stripped.startswith('class '):
                    match = re.search(r'class\s+(\w+)', line)
                    if match:
                        context['classes'].append(match.group(1))
                elif stripped.startswith('def '):
                    match = re.search(r'def\s+(\w+)', line)
                    if match and len(context['functions']) < 25:
                        context['functions'].append(match.group(1))
                elif '=' in stripped and stripped.isupper():
                    match = re.search(r'^([A-Z_]+)\s*=', line)
                    if match and len(context['constants']) < 10:
                        context['constants'].append(match.group(1))
        
        elif language in ['javascript', 'typescript']:
            for line in lines:
                if 'import' in line and 'from' in line:
                    match = re.search(r'from\s+[\'"](.+?)[\'"]', line)
                    if match and len(context['imports']) < 15:
                        context['imports'].append(match.group(1))
                elif 'class ' in line:
                    match = re.search(r'class\s+(\w+)', line)
                    if match:
                        context['classes'].append(match.group(1))
                elif re.search(r'(?:function|const|let|var)\s+(\w+)', line):
                    match = re.search(r'(?:function|const|let|var)\s+(\w+)', line)
                    if match and len(context['functions']) < 25:
                        context['functions'].append(match.group(1))
        
        elif language == 'java':
            for line in lines:
                if 'import ' in line:
                    match = re.search(r'import\s+([\w.]+)', line)
                    if match and len(context['imports']) < 15:
                        context['imports'].append(match.group(1))
                elif 'class ' in line:
                    match = re.search(r'class\s+(\w+)', line)
                    if match:
                        context['classes'].append(match.group(1))
        
        return context
    
    def _chunk_file(self, file_path: str, content: str, language: str,
                    metadata: Dict, file_context: Dict, repo_context: Dict) -> List[Dict]:
        """Chunk a file with context enrichment"""
        
        # Choose chunking strategy
        if language in self.parsers:
            base_chunks = self._semantic_chunk(content, language)
        else:
            base_chunks = self._smart_line_chunk(content)
        
        # Enrich chunks
        enriched_chunks = []
        
        for i, chunk in enumerate(base_chunks):
            enriched_content = self._build_enriched_content(
                chunk, file_path, file_context, repo_context, language
            )
            
            enriched_chunks.append({
                'chunk_id': f"{metadata['repo']}::{file_path}::{i}",
                'repo': metadata['repo'],
                'file_path': file_path,
                'chunk_index': i,
                'content': chunk['content'],
                'enriched_content': enriched_content,
                'chunk_type': chunk['type'],
                'chunk_name': chunk.get('name', f'chunk_{i}'),
                'language': language,
                'start_line': chunk['start_line'],
                'end_line': chunk['end_line'],
                'num_lines': chunk['end_line'] - chunk['start_line'],
                'char_count': len(chunk['content']),
                'hash': hashlib.md5(chunk['content'].encode()).hexdigest(),
                'file_imports': file_context['imports'][:10],
                'file_classes': file_context['classes'],
                'file_functions': file_context['functions'][:15],
                'summary': chunk.get('summary', '')[:300],
            })
        
        return enriched_chunks
    
    def _build_enriched_content(self, chunk: Dict, file_path: str,
                               file_context: Dict, repo_context: Dict, language: str) -> str:
        """Build enriched content with full context for LLM understanding"""
        
        parts = []
        
        # Repository context
        parts.append(f"# Repository: {repo_context['repo_name']}")
        if repo_context['description']:
            parts.append(f"# Description: {repo_context['description']}")
        parts.append(f"# Primary Language: {repo_context['primary_language']}")
        parts.append("")
        
        # File context
        parts.append(f"# File: {file_path}")
        parts.append(f"# Language: {language}")
        
        if file_context['imports']:
            parts.append(f"# Dependencies: {', '.join(file_context['imports'][:5])}")
        
        if file_context['classes']:
            parts.append(f"# Classes: {', '.join(file_context['classes'])}")
        
        if file_context['functions']:
            parts.append(f"# Functions: {', '.join(file_context['functions'][:8])}")
        
        parts.append("")
        
        # Chunk context
        parts.append(f"# Code Section: {chunk.get('name', 'code_block')}")
        parts.append(f"# Type: {chunk['type']}")
        parts.append(f"# Lines: {chunk['start_line']}-{chunk['end_line']}")
        
        if chunk.get('summary'):
            parts.append(f"# Summary: {chunk['summary']}")
        
        parts.append("")
        parts.append("# Code:")
        parts.append(chunk['content'])
        
        return '\n'.join(parts)
    
    def _semantic_chunk(self, content: str, language: str) -> List[Dict]:
        """Semantic chunking using tree-sitter"""
        parser = self.parsers[language]
        tree = parser.parse(bytes(content, 'utf8'))
        
        chunks = []
        lines = content.split('\n')
        
        def extract_name(node):
            for child in node.children:
                if child.type == 'identifier':
                    start = child.start_point
                    end = child.end_point
                    return lines[start[0]][start[1]:end[1]]
            return None
        
        def traverse(node):
            # Target semantic units
            if node.type in ['function_definition', 'class_definition',
                           'method_definition', 'function_declaration',
                           'class_declaration', 'function_item']:
                
                start = max(0, node.start_point[0] - 2)  # Include context
                end = min(len(lines), node.end_point[0] + 2)
                
                chunk_content = '\n'.join(lines[start:end])
                name = extract_name(node) or f"{node.type}_{start}"
                
                chunks.append({
                    'content': chunk_content,
                    'type': node.type,
                    'name': name,
                    'summary': f"{node.type}: {name}",
                    'start_line': start,
                    'end_line': end
                })
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        
        return chunks if chunks else self._smart_line_chunk(content)
    
    def _smart_line_chunk(self, content: str) -> List[Dict]:
        """Smart line-based chunking with overlap"""
        lines = content.split('\n')
        chunks = []
        
        i = 0
        while i < len(lines):
            chunk_start = i
            chunk_end = min(i + self.chunk_size, len(lines))
            
            # Try to end at logical boundaries
            if chunk_end < len(lines) - 5:
                for j in range(chunk_end, max(chunk_end - 20, chunk_start), -1):
                    line = lines[j].strip()
                    if not line or line in ['}', ']', ')'] or line.startswith(('class ', 'def ', 'function ')):
                        chunk_end = j + 1
                        break
            
            chunk_content = '\n'.join(lines[chunk_start:chunk_end])
            
            if chunk_content.strip():
                summary = lines[chunk_start].strip()[:100] if chunk_start < len(lines) else ""
                
                chunks.append({
                    'content': chunk_content,
                    'type': 'code_block',
                    'name': f'lines_{chunk_start}_{chunk_end}',
                    'summary': summary,
                    'start_line': chunk_start,
                    'end_line': chunk_end
                })
            
            # Move forward with overlap
            i = chunk_end - self.overlap_lines if chunk_end < len(lines) else chunk_end
        
        return chunks
    
    def _load_metadata(self, repo_path: str) -> Dict:
        """Load repository metadata"""
        bucket = self.storage_client.bucket(self.bucket_raw)
        blob = bucket.blob(f"{repo_path}/metadata.json")
        return json.loads(blob.download_as_text())
    
    def _read_file(self, blob_path: str) -> str:
        """Read file from Cloud Storage"""
        bucket = self.storage_client.bucket(self.bucket_raw)
        blob = bucket.blob(blob_path)
        return blob.download_as_text()
    
    def _save_chunks(self, repo_path: str, chunks: List[Dict]):
        """Save chunks to Cloud Storage"""
        bucket = self.storage_client.bucket(self.bucket_processed)
        blob = bucket.blob(f"{repo_path}/chunks.jsonl")
        
        jsonl = '\n'.join([json.dumps(chunk) for chunk in chunks])
        blob.upload_from_string(jsonl)