"""
LLM Client using Vertex AI (Gemini 1.5 Pro)
WITH STREAMING SUPPORT
"""
import os
from typing import List, Dict, Iterator
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """Vertex AI Gemini client with streaming support"""

    def __init__(self, project_id: str = None, location: str = None):
        import vertexai
        from vertexai.generative_models import GenerativeModel

        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "otto-pm")
        self.location = location or os.getenv("GCP_REGION", "us-east1")

        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel("gemini-2.5-flash")

        print(f"✓ Vertex AI Gemini initialized")
        print(f"  Project: {self.project_id}, Location: {self.location}")

    def generate(self, prompt: str, temperature: float = 0.2,
                 max_tokens: int = 8192) -> str:
        """Generate text using Vertex AI (non-streaming)"""
        from vertexai.generative_models import GenerationConfig
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
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
            return f"Error: {error_msg[:200]}"

    def generate_stream(self, prompt: str, temperature: float = 0.2,
                        max_tokens: int = 8192) -> Iterator[str]:
        """Generate text with streaming"""
        from vertexai.generative_models import GenerationConfig
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.95,
                    top_k=40,
                ),
                stream=True
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

        return self.generate(
            full_prompt, temperature=temperature, max_tokens=max_tokens)

    def generate_with_context_stream(self, query: str, context_chunks: List[Dict],
                                     system_prompt: str, temperature: float = 0.2,
                                     max_tokens: int = 8192) -> Iterator[str]:
        """Generate response with RAG context (streaming)"""
        context_text = self._build_context(context_chunks)

        full_prompt = f"""{system_prompt}

CONTEXT FROM CODEBASE:
{context_text}

USER QUERY:
{query}

RESPONSE:"""

        yield from self.generate_stream(
            full_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def _build_context(self, chunks: List[Dict], max_chunks: int = 8) -> str:
        """Build context string from chunks"""
        context_parts = []

        for i, chunk in enumerate(chunks[:max_chunks], 1):
            content = chunk.get('enriched_content', chunk.get('content', ''))

            if len(content) > 1500:
                content = content[:1500] + "\n... (truncated)"

            context_parts.append(f"""
--- CHUNK {i} ---
File: {chunk.get('file_path', 'unknown')}
Type: {chunk.get('chunk_type', 'unknown')}

{content}
""")

        return '\n'.join(context_parts)