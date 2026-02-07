"""
Vector search for retrieving relevant code chunks
"""
import json
import numpy as np
from typing import List, Dict, Optional
from google.cloud import storage


class VectorSearch:
    """
    Simple vector search using cosine similarity
    (Can be upgraded to Vertex AI Vector Search later)
    """
    
    def __init__(self, project_id: str, bucket_name: str):
        """
        Initialize vector search
        
        Args:
            project_id: GCP project ID
            bucket_name: Bucket with processed chunks
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.embedding_model = None
        
        self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize embedding model"""
        try:
            from google.cloud import aiplatform
            from vertexai.language_models import TextEmbeddingModel
            
            aiplatform.init(project=self.project_id, location='us-central1')
            self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            print("✓ Embedding model ready")
        except Exception as e:
            print(f"⚠️  Embedding model unavailable: {e}")
    
    def search(self, query: str, repo_path: str, top_k: int = 5,
              filter_language: Optional[str] = None) -> List[Dict]:
        """
        Search for relevant chunks
        
        Args:
            query: Search query
            repo_path: Repository path (owner/repo)
            top_k: Number of results to return
            filter_language: Optional language filter (e.g., 'python')
            
        Returns:
            List of relevant chunks with scores
        """
        # Load chunks
        chunks = self._load_chunks(repo_path)
        
        if not chunks:
            print("⚠️  No chunks found")
            return []
        
        # Filter by language if specified
        if filter_language:
            chunks = [c for c in chunks if c.get('language') == filter_language]
        
        # Check if chunks have embeddings
        has_embeddings = all(c.get('embedding') for c in chunks)
        
        if has_embeddings and self.embedding_model:
            return self._semantic_search(query, chunks, top_k)
        else:
            print("⚠️  Falling back to keyword search (no embeddings)")
            return self._keyword_search(query, chunks, top_k)
    
    def _semantic_search(self, query: str, chunks: List[Dict], top_k: int) -> List[Dict]:
        """Semantic search using embeddings"""
        print(f"🔍 Semantic search for: '{query}'")
        
        # Generate query embedding
        query_embedding = self.embedding_model.get_embeddings([query])[0].values
        
        # Calculate similarities
        results = []
        for chunk in chunks:
            chunk_embedding = chunk['embedding']
            similarity = self._cosine_similarity(query_embedding, chunk_embedding)
            
            results.append({
                'chunk': chunk,
                'score': similarity
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return [r['chunk'] for r in results[:top_k]]
    
    def _keyword_search(self, query: str, chunks: List[Dict], top_k: int) -> List[Dict]:
        """Fallback keyword search"""
        print(f"🔍 Keyword search for: '{query}'")
        
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        results = []
        for chunk in chunks:
            content = chunk.get('enriched_content', chunk.get('content', '')).lower()
            
            # Count matching terms
            matches = sum(1 for term in query_terms if term in content)
            
            if matches > 0:
                results.append({
                    'chunk': chunk,
                    'score': matches / len(query_terms)
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return [r['chunk'] for r in results[:top_k]]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return float(dot_product / (norm1 * norm2))
    
    def _load_chunks(self, repo_path: str) -> List[Dict]:
        """Load chunks from GCS"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"{repo_path}/chunks.jsonl")
            content = blob.download_as_text()
            
            chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
            print(f"✓ Loaded {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            print(f"❌ Error loading chunks: {e}")
            return []