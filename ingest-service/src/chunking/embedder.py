"""
Pure embedding module - Adds embeddings to existing chunks
"""
import json
import time
from typing import List, Dict, Optional
from google.cloud import storage


class ChunkEmbedder:
    """
    Generate and add embeddings to chunks
    Handles: Load Chunks → Generate Embeddings → Save Updated Chunks
    """
    
    def __init__(self, project_id: str, bucket_processed: str, location: str = 'us-central1'):
        """
        Initialize the embedder
        
        Args:
            project_id: GCP project ID
            bucket_processed: Bucket with processed chunks
            location: GCP region for Vertex AI
        """
        self.project_id = project_id
        self.bucket_processed = bucket_processed
        self.location = location
        
        self.storage_client = storage.Client(project=project_id)
        self.embedding_model = None
        
        # Embedding settings
        self.batch_size = 25
        self.max_text_length = 1000  # chars per embedding
    
    def initialize_model(self, timeout: int = 100) -> bool:
        """
        Initialize Vertex AI embedding model
        
        Args:
            timeout: Initialization timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if self.embedding_model is not None:
            return True
        
        try:
            print(f"🔄 Initializing Vertex AI embedding model...")
            print(f"   Region: {self.location}")
            print(f"   Timeout: {timeout}s")
            
            from google.cloud import aiplatform
            from vertexai.language_models import TextEmbeddingModel
            
            aiplatform.init(project=self.project_id, location=self.location)
            self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            
            print("✓ Embedding model ready")
            return True
            
        except Exception as e:
            print(f"❌ Embedding initialization failed: {str(e)[:100]}")
            print("   Possible causes:")
            print("   - Network/DNS issues")
            print("   - Vertex AI API not enabled")
            print("   - Authentication problems")
            return False
    
    def embed_repository(self, repo_path: str, force_reembed: bool = False) -> Dict:
        """
        Add embeddings to all chunks in a repository
        
        Args:
            repo_path: Repository path (owner/repo)
            force_reembed: Re-embed chunks that already have embeddings
            
        Returns:
            Statistics dictionary
        """
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"🎯 EMBEDDING: {repo_path}")
        print(f"{'='*60}")
        
        # Load chunks
        chunks = self._load_chunks(repo_path)
        print(f"📦 Loaded: {len(chunks)} chunks")
        
        # Check existing embeddings
        already_embedded = sum(1 for c in chunks if c.get('embedding'))
        
        if already_embedded > 0 and not force_reembed:
            print(f"✓ {already_embedded} chunks already have embeddings")
            print(f"  Use --force to re-embed all chunks")
            chunks_to_embed = [c for c in chunks if not c.get('embedding')]
        else:
            chunks_to_embed = chunks
        
        print(f"🎯 Chunks to embed: {len(chunks_to_embed)}")
        
        if len(chunks_to_embed) == 0:
            print("✓ Nothing to do")
            return {'total': len(chunks), 'embedded': already_embedded, 'new': 0}
        
        # Initialize model
        if not self.initialize_model():
            print("❌ Cannot proceed without embedding model")
            return {'total': len(chunks), 'embedded': 0, 'new': 0, 'failed': len(chunks_to_embed)}
        
        # Generate embeddings
        stats = self._generate_embeddings_batch(chunks_to_embed)
        
        # Save updated chunks
        self._save_chunks(repo_path, chunks)
        
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ EMBEDDING COMPLETE")
        print(f"{'='*60}")
        print(f"Total chunks: {len(chunks)}")
        print(f"Already embedded: {already_embedded}")
        print(f"Newly embedded: {stats['success']}")
        print(f"Failed: {stats['failed']}")
        print(f"Time: {elapsed:.1f}s")
        if stats['success'] > 0:
            print(f"Speed: {stats['success']/elapsed:.1f} embeddings/sec")
        
        return {
            'total': len(chunks),
            'already_embedded': already_embedded,
            'newly_embedded': stats['success'],
            'failed': stats['failed']
        }
    
    def _generate_embeddings_batch(self, chunks: List[Dict]) -> Dict:
        """Generate embeddings in batches"""
        print(f"\n🔄 Generating embeddings (batch size: {self.batch_size})...")
        
        success_count = 0
        failed_count = 0
        start_time = time.time()
        
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            
            # Prepare texts (use enriched content, truncate if needed)
            batch_texts = []
            for chunk in batch:
                text = chunk.get('enriched_content', chunk['content'])
                if len(text) > self.max_text_length:
                    text = text[:self.max_text_length]
                batch_texts.append(text)
            
            try:
                # Generate embeddings
                embeddings = self.embedding_model.get_embeddings(batch_texts)
                
                # Assign to chunks
                for j, chunk in enumerate(batch):
                    if j < len(embeddings):
                        chunk['embedding'] = embeddings[j].values
                        chunk['embedding_model'] = 'text-embedding-004'
                        chunk['embedding_dim'] = len(embeddings[j].values)
                        success_count += 1
                
                # Progress
                if (i // self.batch_size + 1) % 5 == 0:
                    elapsed = time.time() - start_time
                    rate = success_count / elapsed if elapsed > 0 else 0
                    print(f"  ✓ {success_count}/{len(chunks)} ({rate:.1f}/sec)")
                    
            except Exception as e:
                failed_count += len(batch)
                error_msg = str(e)[:60]
                
                if "Timeout" in error_msg or "DNS" in error_msg:
                    print(f"  ⚠️  Batch {i//self.batch_size + 1}: Network timeout, skipping...")
                elif "quota" in error_msg.lower():
                    print(f"  ⚠️  Quota exceeded, stopping...")
                    break
                else:
                    print(f"  ⚠️  Batch {i//self.batch_size + 1}: {error_msg}")
        
        return {'success': success_count, 'failed': failed_count}
    
    def _load_chunks(self, repo_path: str) -> List[Dict]:
        """Load chunks from Cloud Storage"""
        bucket = self.storage_client.bucket(self.bucket_processed)
        blob = bucket.blob(f"{repo_path}/chunks.jsonl")
        
        content = blob.download_as_text()
        return [json.loads(line) for line in content.split('\n') if line.strip()]
    
    def _save_chunks(self, repo_path: str, chunks: List[Dict]):
        """Save updated chunks back to Cloud Storage"""
        bucket = self.storage_client.bucket(self.bucket_processed)
        blob = bucket.blob(f"{repo_path}/chunks.jsonl")
        
        jsonl = '\n'.join([json.dumps(chunk) for chunk in chunks])
        blob.upload_from_string(jsonl)
        
        print(f"💾 Saved to: gs://{self.bucket_processed}/{repo_path}/chunks.jsonl")