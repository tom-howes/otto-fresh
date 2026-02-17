# ingest-service/src/rag/vector_search.py
"""
Fast vector search using Vertex AI embeddings
"""
import json
import numpy as np
import time
from typing import List, Dict, Optional
from google.cloud import storage
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel


class VectorSearch:
    """Fast semantic search using Vertex AI embeddings"""
    
    def __init__(self, project_id: str, bucket_name: str, location: str = 'us-central1'):
        self.client = storage.Client(project=project_id)
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(bucket_name)
        self.project_id = project_id
        self.location = location
        self.model = None
        
        # Initialize Vertex AI
        try:
            aiplatform.init(project=project_id, location=location)
            print(f"✓ Vertex AI initialized (project: {project_id}, location: {location})")
        except Exception as e:
            print(f"⚠️  Vertex AI init warning: {e}")
    
    def _get_model(self):
        """Lazy load the embedding model"""
        if self.model is None:
            self.model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            print("✓ Loaded text-embedding-004 model")
        return self.model
    
    def _embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query using Vertex AI (FAST)"""
        try:
            model = self._get_model()
            embeddings = model.get_embeddings([query])
            return embeddings[0].values
        except Exception as e:
            print(f"❌ Query embedding failed: {e}")
            raise
    
    def search(self, query: str, repo_path: str, top_k: int = 5, 
               filter_language: Optional[str] = None) -> List[Dict]:
        """
        Search for most relevant chunks using semantic similarity.
        
        Args:
            query: Search query text
            repo_path: Path to repository chunks in GCS (e.g., 'repos/owner/repo')
            top_k: Number of top results to return
            filter_language: Optional language filter (e.g., 'python', 'javascript')
            
        Returns:
            List of most relevant chunks with similarity scores, sorted by relevance
        """
        print(f"🔍 Searching in: {repo_path}")
        print(f"   Query: {query}")
        print(f"   Top K: {top_k}")
        
        # Load chunks from GCS
        blob = self.bucket.blob(f"{repo_path}/chunks.jsonl")
        if not blob.exists():
            print(f"❌ No chunks found at: {repo_path}/chunks.jsonl")
            return []
        
        content = blob.download_as_text()
        chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
        print(f"✓ Loaded {len(chunks)} chunks")
        
        # Filter by language if specified
        if filter_language:
            chunks = [c for c in chunks if c.get('language', '').lower() == filter_language.lower()]
            print(f"✓ Filtered to {len(chunks)} chunks for language: {filter_language}")
        
        # Get chunks that have embeddings
        chunks_with_embeddings = [c for c in chunks if c.get('embedding')]
        print(f"✓ Found {len(chunks_with_embeddings)} chunks with embeddings")
        
        if not chunks_with_embeddings:
            print("⚠️  No chunks with embeddings found")
            return []
        
        # Generate embedding for the query (FAST with Vertex AI)
        print(f"🔄 Generating query embedding...")
        query_start = time.time()
        try:
            query_embedding = self._embed_query(query)
            query_time = time.time() - query_start
            print(f"✓ Query embedded in {query_time:.2f}s (dim: {len(query_embedding)})")
        except Exception as e:
            print(f"❌ Failed to embed query: {e}")
            raise
        
        # Calculate cosine similarity for each chunk
        print(f"🔄 Calculating similarities...")
        similarities = []
        for chunk in chunks_with_embeddings:
            chunk_embedding = chunk['embedding']
            similarity = self._cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((similarity, chunk))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[0], reverse=True)
        if similarities:
            print(f"✓ Top similarity score: {similarities[0][0]:.4f}")
        
        # Return top k results
        results = []
        for similarity, chunk in similarities[:top_k]:
            chunk_copy = chunk.copy()
            chunk_copy['similarity_score'] = float(similarity)
            
            # Remove embedding from result to reduce payload size
            if 'embedding' in chunk_copy:
                del chunk_copy['embedding']
            
            results.append(chunk_copy)
        
        print(f"✓ Returning {len(results)} results")
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Cosine similarity ranges from -1 (opposite) to 1 (identical).
        0 means orthogonal (no similarity).
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (float)
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # Calculate dot product
        dot_product = np.dot(v1, v2)
        
        # Calculate norms (magnitudes)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        # Avoid division by zero
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity = dot product / (norm1 * norm2)
        return float(dot_product / (norm1 * norm2))
    
    def batch_search(self, queries: List[str], repo_path: str, top_k: int = 5) -> Dict[str, List[Dict]]:
        """
        Perform multiple searches at once (more efficient for multiple queries).
        
        Args:
            queries: List of search queries
            repo_path: Path to repository chunks
            top_k: Number of results per query
            
        Returns:
            Dictionary mapping each query to its results
        """
        results = {}
        for query in queries:
            try:
                results[query] = self.search(query, repo_path, top_k)
            except Exception as e:
                print(f"⚠️  Failed to search for '{query}': {e}")
                results[query] = []
        return results
    
    def get_chunk_stats(self, repo_path: str) -> Dict:
        """
        Get statistics about chunks in a repository.
        
        Args:
            repo_path: Path to repository chunks
            
        Returns:
            Dictionary with stats (total chunks, embedded chunks, languages, etc.)
        """
        blob = self.bucket.blob(f"{repo_path}/chunks.jsonl")
        if not blob.exists():
            return {
                'exists': False,
                'total_chunks': 0,
                'embedded_chunks': 0
            }
        
        content = blob.download_as_text()
        chunks = [json.loads(line) for line in content.split('\n') if line.strip()]
        
        embedded_chunks = [c for c in chunks if c.get('embedding')]
        languages = set(c.get('language') for c in chunks if c.get('language'))
        chunk_types = set(c.get('chunk_type') for c in chunks if c.get('chunk_type'))
        
        return {
            'exists': True,
            'total_chunks': len(chunks),
            'embedded_chunks': len(embedded_chunks),
            'embedding_coverage': len(embedded_chunks) / len(chunks) if chunks else 0,
            'languages': list(languages),
            'chunk_types': list(chunk_types),
            'ready_for_search': len(embedded_chunks) > 0
        }