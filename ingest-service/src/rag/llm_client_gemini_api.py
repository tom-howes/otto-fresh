"""
LLM Client using Gemini API directly (not Vertex AI)
Free tier: 15 requests/min, 1M tokens/day
WITH STREAMING SUPPORT
"""
import os
from typing import List, Dict, Iterator
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """Direct Gemini API client with streaming support"""
    
    def __init__(self, project_id: str = None, location: str = None):
        """
        Initialize Gemini API client
        
        Note: Ignores project_id/location, uses API key instead
        Get your key from: https://aistudio.google.com/app/apikey
        """
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment.\n"
                "Get your free API key from: https://aistudio.google.com/app/apikey\n"
                "Then add to .env file: GEMINI_API_KEY=your_key_here"
            )
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Flash (free tier)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        print("✓ Gemini API initialized (free tier)")
        print("  Limits: 15 requests/min, 1M tokens/day")
    
    def generate(self, prompt: str, temperature: float = 0.2, 
                max_tokens: int = 8192) -> str:
        """Generate text using Gemini API (non-streaming)"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.95,
                    top_k=40,
                )
            )
            
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Generation error: {error_msg}")
            
            if "API_KEY" in error_msg.upper():
                return "Error: Invalid API key. Get one from https://aistudio.google.com/app/apikey"
            elif "RATE_LIMIT" in error_msg.upper():
                return "Error: Rate limit exceeded (15 req/min on free tier)"
            elif "QUOTA" in error_msg.upper():
                return "Error: Daily quota exceeded (1M tokens/day on free tier)"
            else:
                return f"Error: {error_msg[:200]}"
    
    def generate_stream(self, prompt: str, temperature: float = 0.2,
                       max_tokens: int = 8192) -> Iterator[str]:
        """
        Generate text with streaming (yields chunks as they arrive)
        
        Args:
            prompt: Input prompt
            temperature: Creativity level
            max_tokens: Maximum output length
            
        Yields:
            Text chunks as they are generated
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.95,
                    top_k=40,
                ),
                stream=True  # Enable streaming
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            error_msg = str(e)
            yield f"\n⚠️  Error during generation: {error_msg[:200]}\n"
    
    def generate_with_context(self, query: str, context_chunks: List[Dict],
                             system_prompt: str, temperature: float = 0.2,
                             max_tokens: int = 8192) -> str:
        """Generate response with RAG context (non-streaming)"""
        context_text = self._build_context(context_chunks)
        
        full_prompt = f"""{system_prompt}

CONTEXT FROM CODEBASE:
{context_text}

USER QUERY:
{query}

RESPONSE:"""
        
        return self.generate(full_prompt, temperature=temperature, max_tokens=max_tokens)
    
    def generate_with_context_stream(self, query: str, context_chunks: List[Dict],
                                     system_prompt: str, temperature: float = 0.2,
                                     max_tokens: int = 8192) -> Iterator[str]:
        """
        Generate response with RAG context (streaming)
        
        Yields text chunks as they are generated
        """
        context_text = self._build_context(context_chunks)
        
        full_prompt = f"""{system_prompt}

CONTEXT FROM CODEBASE:
{context_text}

USER QUERY:
{query}

RESPONSE:"""
        
        yield from self.generate_stream(full_prompt, temperature=temperature, max_tokens=max_tokens)
    
    def _build_context(self, chunks: List[Dict], max_chunks: int = 8) -> str:
        """Build context string from chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks[:max_chunks], 1):
            content = chunk.get('enriched_content', chunk.get('content', ''))
            
            # Truncate to save tokens
            if len(content) > 1500:
                content = content[:1500] + "\n... (truncated)"
            
            context_parts.append(f"""
--- CHUNK {i} ---
File: {chunk.get('file_path', 'unknown')}
Type: {chunk.get('chunk_type', 'unknown')}

{content}
""")
        
        return '\n'.join(context_parts)