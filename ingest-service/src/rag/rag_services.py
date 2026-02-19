# ingest-service/src/rag/rag_services.py
"""
RAG Services with SMART FILE DETECTION
Automatically detects target files for code completion and editing
"""
from typing import List, Dict, Optional, Iterator
from .llm_client_gemini_api import GeminiClient
from .vector_search import VectorSearch
from ..github.github_client import GitHubClient
from ..utils.file_manager import DocumentationManager
import re
import time


class RAGServices:
    """
    Complete RAG system with intelligent file detection
    """
    
    def __init__(self, project_id: str, bucket_processed: str,
                 enable_github: bool = True, enable_local_save: bool = True):
        self.llm = GeminiClient(project_id)
        self.search = VectorSearch(project_id, bucket_processed)
        self.project_id = project_id
        self.bucket_name = bucket_processed
        
        self.enable_github = enable_github
        self.github_client = None  # Set externally with user's token
        
        self.enable_local_save = enable_local_save
        if enable_local_save:
            self.doc_manager = DocumentationManager()
    
    # ==================== SMART FILE DETECTION ====================
    
    def _detect_target_file(self, code_context: str, repo_path: str, 
                           language: str = 'python') -> Optional[Dict]:
        """
        Intelligently detect which file the code context belongs to.
        
        Uses semantic search to find the most similar code in the repository.
        
        Args:
            code_context: The code snippet
            repo_path: Repository path
            language: Programming language
            
        Returns:
            Dict with file_path, similarity, and metadata, or None if not found
        """
        print(f"\n🔍 AUTO-DETECTING target file...")
        print(f"   Code context: {code_context[:60]}...")
        print(f"   Language: {language}")
        
        # Search for similar code
        results = self.search.search(
            query=code_context,
            repo_path=repo_path,
            top_k=5,
            filter_language=language
        )
        
        if not results:
            print(f"❌ No similar code found")
            return None
        
        # Get the file with highest similarity
        best_match = results[0]
        target_file = best_match['file_path']
        similarity = best_match.get('similarity_score', 0)
        
        print(f"✓ Detected target file: {target_file}")
        print(f"  Similarity: {similarity:.3f}")
        print(f"  Match type: {best_match['chunk_type']}")
        print(f"  Lines: {best_match['start_line']}-{best_match['end_line']}")
        
        # Require reasonable similarity (>0.6) to be confident
        if similarity < 0.6:
            print(f"⚠️  Low similarity ({similarity:.3f}) - might not be correct file")
            return None
        
        return {
            'file_path': target_file,
            'similarity': similarity,
            'chunk_type': best_match['chunk_type'],
            'lines': f"{best_match['start_line']}-{best_match['end_line']}",
            'confidence': 'high' if similarity > 0.8 else 'medium'
        }

    # ==================== NEW: SURGICAL EDIT HELPERS ====================

    def _get_existing_file_content(self, repo_path: str, file_path: str) -> Optional[str]:
        """
        Fetch the actual current content of a file from GitHub.
        
        Args:
            repo_path: Repository path (repos/owner/repo or owner/repo)
            file_path: Path to the file within the repo
            
        Returns:
            File content as string, or None if fetch failed
        """
        if self.github_client:
            clean_repo_path = repo_path.replace('repos/', '')
            content = self.github_client.get_file_content(clean_repo_path, file_path)
            if content:
                print(f"✓ Fetched existing file from GitHub ({len(content)} chars)")
            else:
                print(f"⚠️  Could not fetch {file_path} from GitHub")
            return content
        print(f"⚠️  No GitHub client available to fetch file")
        return None

    def _insert_completion_into_file(self, existing_content: str,
                                      code_context: str, completion: str) -> str:
        """
        Insert completion into the existing file at the correct position.
        
        Finds where code_context appears in the file and appends
        the completion immediately after it, preserving everything else.
        
        Args:
            existing_content: Full current file content from GitHub
            code_context: The code snippet the user provided (used to locate insertion point)
            completion: The generated completion to insert
            
        Returns:
            Full file content with completion inserted at the right position
        """
        context_stripped = code_context.strip()
        
        if context_stripped in existing_content:
            idx = existing_content.index(context_stripped)
            insert_at = idx + len(context_stripped)
            print(f"✓ Insertion point found at character {insert_at}")
            return (
                existing_content[:insert_at]
                + "\n"
                + completion
                + existing_content[insert_at:]
            )
        else:
            # Fallback: append at end of file with a separator comment
            print("⚠️  Could not locate exact context in file, appending at end")
            return existing_content.rstrip() + "\n\n" + completion
    
    # ==================== Q&A SERVICE ====================
    
    def answer_question(self, question: str, repo_path: str, 
                       language: Optional[str] = None,
                       stream: bool = False) -> Dict:
        """Answer questions about the codebase"""
        print(f"\n{'='*60}")
        print(f"❓ Q&A SERVICE {('(Streaming)' if stream else '')}")
        print(f"{'='*60}")
        print(f"Question: {question}")
        
        chunks = self.search.search(question, repo_path, top_k=8, filter_language=language)
        
        if not chunks:
            return {
                'answer': "I couldn't find relevant information in the codebase.",
                'sources': [],
                'chunks_used': 0
            }
        
        system_prompt = """You are an expert code assistant. Answer the user's question based ONLY on the provided code context.

Instructions:
- Be precise and technical
- Reference specific files and line numbers when relevant
- If the answer isn't in the context, say so
- Provide code examples when relevant
- Explain complex concepts clearly
"""
        
        sources = [
            {
                'file': c['file_path'],
                'lines': f"{c['start_line']}-{c['end_line']}",
                'type': c['chunk_type'],
                'similarity': c.get('similarity_score', 0)
            }
            for c in chunks[:5]
        ]
        
        if stream:
            return {
                'answer_stream': self.llm.generate_with_context_stream(
                    question, chunks, system_prompt, temperature=0.2, max_tokens=4096
                ),
                'sources': sources,
                'streaming': True
            }
        else:
            answer = self.llm.generate_with_context(
                question, chunks, system_prompt, temperature=0.2, max_tokens=4096
            )
            
            print(f"✓ Answer generated with {len(sources)} sources")
            
            return {
                'answer': answer,
                'sources': sources,
                'chunks_used': len(chunks)
            }
    
    # ==================== DOCUMENTATION SERVICE ====================
    
    def generate_documentation(self, target: str, repo_path: str,
                              doc_type: str = 'api',
                              stream: bool = False,
                              push_to_github: bool = False,
                              save_local: bool = True) -> Dict:
        """Generate professional documentation"""
        print(f"\n{'='*60}")
        print(f"📝 DOCUMENTATION SERVICE")
        print(f"{'='*60}")
        print(f"Target: {target}")
        print(f"Type: {doc_type}")
        
        query = f"documentation for {target} functions classes methods"
        chunks = self.search.search(query, repo_path, top_k=10)
        
        if not chunks:
            return {
                'documentation': "No relevant code found to document.",
                'type': doc_type,
                'files_referenced': 0
            }
        
        prompts = {
            'api': """Generate comprehensive API documentation in Markdown format.

Include:
1. **Overview and Purpose** - What this API does
2. **Functions/Classes** - Full signatures with all parameters
3. **Parameters** - Type, description, required/optional
4. **Return Values** - Types and descriptions
5. **Usage Examples** - Practical code examples
6. **Error Handling** - What exceptions can be raised
7. **Common Use Cases** - Real-world scenarios

Be thorough and complete.""",
            
            'user_guide': """Generate a comprehensive user guide in Markdown format.

Include:
1. **Introduction** - Clear overview
2. **Getting Started** - Prerequisites and setup
3. **Step-by-Step Instructions**
4. **Common Use Cases**
5. **Troubleshooting**
6. **Best Practices**
7. **FAQ**

Be detailed and user-friendly.""",
            
            'technical': """Generate detailed technical documentation in Markdown format.

Include:
1. **Architecture Overview**
2. **Implementation Details**
3. **Design Patterns**
4. **Dependencies**
5. **Performance Considerations**
6. **Code Examples**
7. **Technical Constraints**

Be thorough and technical.""",
            
            'readme': """Generate a comprehensive README.md.

Include:
1. **Project Title and Description**
2. **Features**
3. **Installation**
4. **Usage**
5. **API Reference**
6. **Configuration**
7. **Contributing**
8. **License**

Be complete and professional."""
        }
        
        system_prompt = prompts.get(doc_type, prompts['api'])
        full_query = f"Generate COMPLETE {doc_type} documentation for: {target}"
        
        if stream:
            return {
                'documentation_stream': self.llm.generate_with_context_stream(
                    full_query, chunks, system_prompt, temperature=0.3, max_tokens=8192
                ),
                'type': doc_type,
                'files_referenced': len(set(c['file_path'] for c in chunks)),
                'streaming': True
            }
        else:
            docs = self.llm.generate_with_context(
                full_query, chunks, system_prompt, temperature=0.3, max_tokens=8192
            )
            
            result = {
                'documentation': docs,
                'type': doc_type,
                'files_referenced': len(set(c['file_path'] for c in chunks))
            }
            
            if save_local and self.enable_local_save:
                local_path = self.doc_manager.save_documentation(docs, target, doc_type, repo_path)
                result['local_file'] = local_path
                print(f"✓ Saved locally: {local_path}")
            
            if push_to_github and self.enable_github and self.github_client:
                print("\n📤 Pushing documentation to GitHub...")
                clean_repo_path = repo_path.replace('repos/', '')
                github_result = self.github_client.push_documentation(
                    clean_repo_path, docs, target, doc_type, create_pr=True
                )
                result['github'] = github_result
                
                if github_result.get('success'):
                    print(f"✓ GitHub PR created: {github_result.get('pr_url')}")
                else:
                    print(f"❌ GitHub push failed: {github_result.get('error')}")
            
            return result
    
    # ==================== CODE COMPLETION WITH AUTO FILE DETECTION ====================
    
    def complete_code(self, code_context: str, cursor_position: str,
                     repo_path: str, language: str = 'python',
                     stream: bool = False,
                     push_to_github: bool = False,
                     save_local: bool = False,
                     target_file: Optional[str] = None) -> Dict:
        """
        Intelligent code completion with AUTOMATIC file detection.
        
        If target_file is not provided and push_to_github=True,
        Otto will automatically detect the most relevant file based on
        semantic similarity to existing code in the repository.
        
        Args:
            code_context: Code before cursor
            cursor_position: Current position info
            repo_path: Repository path
            language: Programming language
            stream: Enable streaming
            push_to_github: Create PR with completed code
            save_local: Save locally
            target_file: File being edited (auto-detected if not provided)
        """
        print(f"\n{'='*60}")
        print(f"💻 CODE COMPLETION WITH SMART FILE DETECTION")
        print(f"{'='*60}")
        print(f"Language: {language}")
        print(f"Push to GitHub: {push_to_github}")
        print(f"Target file provided: {target_file is not None}")
        
        # ===== AUTO-DETECT target file if not provided =====
        detection_info = None
        if not target_file:
            if push_to_github:
                print(f"\n🤖 Auto-detecting target file (required for GitHub push)...")
                detection_info = self._detect_target_file(code_context, repo_path, language)
                
                if detection_info:
                    target_file = detection_info['file_path']
                    print(f"✓ Will push to: {target_file}")
                    print(f"  Confidence: {detection_info['confidence']}")
                else:
                    print(f"❌ Could not auto-detect file with sufficient confidence")
                    return {
                        'completion': None,
                        'language': language,
                        'confidence': 'low',
                        'detected_file': None,
                        'error': 'Could not auto-detect target file. Code context may be too generic or not similar enough to any file in the repository.',
                        'suggestion': 'Either provide "target_file" explicitly or use more specific code context that matches existing code in your repository.',
                        'help': 'Try using a more complete function signature or include unique identifiers from your codebase.'
                    }
            else:
                # Not pushing to GitHub, target_file not required
                print(f"ℹ️  Target file not provided (not needed for preview mode)")
        
        # Search for similar code patterns
        query = f"{language} code similar to: {code_context[-200:]}"
        chunks = self.search.search(query, repo_path, top_k=5, filter_language=language)
        
        print(f"✓ Found {len(chunks)} similar code patterns")
        
        # Build context from similar chunks
        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"# From {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']}):\n"
                f"{chunk['content'][:500]}"
            )
        context = "\n\n".join(context_parts)
        
        # ===== UPDATED PROMPT: complete only the snippet, not the whole file =====
        system_prompt = f"""You are an expert {language} code completion assistant.

Your job is to complete ONLY the provided code snippet — do NOT rewrite the entire file.

Rules:
- Return ONLY the completion (the lines that come after the provided snippet)
- Match the coding style, indentation, and patterns from the repository examples
- Use type hints if the codebase uses them
- Do NOT repeat the input code_context in your response
- Do NOT include any explanation, markdown prose, or file-level boilerplate
- Just return the raw completion code
"""
        
        completion_query = f"""Complete this {language} code snippet:
```{language}
{code_context}
```

Repository patterns for style reference:
{context}

Return ONLY the lines that complete the snippet above. Do not repeat the snippet itself.
"""
        
        if stream:
            return {
                'completion_stream': self.llm.generate_with_context_stream(
                    completion_query, chunks, system_prompt, temperature=0.3, max_tokens=1024
                ),
                'language': language,
                'streaming': True,
                'detected_file': detection_info['file_path'] if detection_info else None,
                'detection_confidence': detection_info['confidence'] if detection_info else None
            }
        else:
            completion = self.llm.generate_with_context(
                completion_query, chunks, system_prompt, temperature=0.3, max_tokens=1024
            )
            
            print(f"✓ Completion generated ({len(completion)} chars)")
            
            # Extract code from response
            code_content = self._extract_code_from_response(completion)

            # ===== SURGICAL INSERT: fetch real file, insert at correct position =====
            full_code = None
            if target_file:
                existing_content = self._get_existing_file_content(repo_path, target_file)
                if existing_content:
                    full_code = self._insert_completion_into_file(
                        existing_content, code_context, code_content
                    )
                    print(f"✓ Inserted into existing file "
                          f"({len(existing_content)} → {len(full_code)} chars)")
                else:
                    print(f"⚠️  Could not fetch existing file, using context + completion only")
                    full_code = code_context + "\n" + code_content
            else:
                # Preview mode - no file needed
                full_code = code_context + "\n" + code_content
            
            result = {
                'completion': completion,
                'language': language,
                'confidence': 'high' if len(chunks) >= 3 else 'medium',
                'patterns_found': len(chunks),
                'detected_file': detection_info['file_path'] if detection_info else target_file,
                'detection_confidence': detection_info['confidence'] if detection_info else 'provided',
                'detection_similarity': detection_info['similarity'] if detection_info else None
            }
            
            # Push to GitHub if requested
            if push_to_github and self.enable_github and self.github_client:
                if not target_file:
                    result['github_error'] = "Could not auto-detect target file with sufficient confidence"
                    print("❌ Cannot push to GitHub: target file detection failed")
                else:
                    print(f"\n📤 Pushing code completion to GitHub...")
                    print(f"   Target file: {target_file}")
                    if detection_info:
                        print(f"   Detection method: Auto-detected")
                        print(f"   Confidence: {detection_info['confidence']}")
                        print(f"   Similarity: {detection_info['similarity']:.3f}")
                    else:
                        print(f"   Detection method: Explicitly provided")
                    
                    # Clean repo path
                    clean_repo_path = repo_path.replace('repos/', '')
                    
                    try:
                        github_result = self.github_client.create_branch_and_push_code(
                            repo_path=clean_repo_path,
                            file_path=target_file,
                            new_content=full_code,
                            instruction=f"🤖 AI code completion: {code_context[:60]}..."
                        )
                        result['github'] = github_result
                        
                        if github_result.get('success'):
                            print(f"✓ Branch created: {github_result['branch']}")
                            if github_result.get('pr_url'):
                                print(f"✓ Pull request: {github_result['pr_url']}")
                        else:
                            print(f"❌ GitHub push failed: {github_result.get('error')}")
                    except Exception as e:
                        print(f"❌ GitHub push exception: {e}")
                        result['github_error'] = str(e)
            
            # Save locally
            if save_local and self.enable_local_save and target_file:
                try:
                    local_path = self.doc_manager.save_edited_code(
                        full_code, target_file, repo_path, "code completion"
                    )
                    result['local_file'] = local_path
                    print(f"✓ Saved locally: {local_path}")
                except Exception as e:
                    print(f"⚠️  Failed to save locally: {e}")
            
            return result
    
    # ==================== CODE EDITING ====================
    
    def edit_code(self, instruction: str, target_file: Optional[str],
                  repo_path: str, stream: bool = False,
                  push_to_github: bool = False,
                  save_local: bool = True) -> Dict:
        """
        Edit existing code based on natural language instructions.
        NOW SUPPORTS AUTO FILE DETECTION!
        
        If target_file is not provided, Otto will detect it from the instruction.
        
        Args:
            instruction: What to change (natural language)
            target_file: File to edit (auto-detected if None)
            repo_path: Repository path
            stream: Enable streaming
            push_to_github: Create PR with changes
            save_local: Save edited code locally
        """
        print(f"\n{'='*60}")
        print(f"✏️  CODE EDITING WITH SMART FILE DETECTION")
        print(f"{'='*60}")
        print(f"Instruction: {instruction}")
        print(f"Target file provided: {target_file is not None}")
        
        # ===== AUTO-DETECT target file if not provided =====
        detection_info = None
        if not target_file:
            print(f"\n🤖 Auto-detecting target file from instruction...")
            detection_info = self._detect_target_file(instruction, repo_path, 'python')
            
            if detection_info:
                target_file = detection_info['file_path']
                print(f"✓ Detected target file: {target_file}")
                print(f"  Confidence: {detection_info['confidence']}")
            else:
                print(f"❌ Could not auto-detect file")
                return {
                    'error': 'Could not auto-detect target file from instruction.',
                    'modified_code': None,
                    'instruction': instruction,
                    'chunks_analyzed': 0,
                    'suggestion': 'Provide "target_file" explicitly or include file name/path in instruction.'
                }
        
        print(f"\n📝 Target: {target_file}")

        # ===== FETCH ACTUAL FILE CONTENT FROM GITHUB =====
        existing_content = self._get_existing_file_content(repo_path, target_file)

        # Search for the target file chunks (used as fallback + extra context)
        query = f"{target_file} {instruction}"
        chunks = self.search.search(query, repo_path, top_k=10)
        
        # Filter to target file chunks
        target_chunks = [c for c in chunks if target_file in c['file_path']]
        
        if not target_chunks and not existing_content:
            print(f"❌ File {target_file} not found in indexed code or GitHub")
            return {
                'error': f"File {target_file} not found in indexed code",
                'modified_code': None,
                'file': target_file,
                'instruction': instruction,
                'chunks_analyzed': 0,
                'detected_file': detection_info['file_path'] if detection_info else None
            }
        
        # Get surrounding context from other files for style reference
        other_chunks = [c for c in chunks if target_file not in c['file_path']][:3]
        all_chunks = target_chunks + other_chunks
        
        print(f"✓ Found {len(target_chunks)} chunks from {target_file}")

        # Use actual GitHub file if available, otherwise reconstruct from chunks
        file_content_for_prompt = existing_content if existing_content else \
            "\n\n".join([c['content'] for c in target_chunks])

        # ===== UPDATED PROMPT: surgical edit only, full file returned =====
        system_prompt = """You are an expert code editor making SURGICAL edits only.

Rules:
- Return the COMPLETE file content with ONLY the requested changes applied
- Do NOT rewrite, reorganize, or touch unrelated functions or classes
- Preserve ALL existing imports, comments, docstrings, and code structure exactly
- Only modify precisely what the instruction asks for
- Maintain the exact indentation and coding style of the surrounding code
- Return the full modified file in a single code block
"""
        
        edit_query = f"""Instruction: {instruction}

Current complete file content ({target_file}):
```
{file_content_for_prompt}
```

Apply ONLY the change described in the instruction above.
Return the COMPLETE modified file with the minimal diff — touch only what is needed.
"""
        
        if stream:
            return {
                'modified_code_stream': self.llm.generate_with_context_stream(
                    edit_query, all_chunks, system_prompt, temperature=0.2, max_tokens=8192
                ),
                'file': target_file,
                'instruction': instruction,
                'streaming': True,
                'detected_file': detection_info['file_path'] if detection_info else None
            }
        else:
            response = self.llm.generate_with_context(
                edit_query, all_chunks, system_prompt, temperature=0.2, max_tokens=8192
            )
            
            code_content = self._extract_code_from_response(response)
            print(f"✓ Edit generated ({len(code_content)} chars)")
            
            result = {
                'modified_code': response,
                'file': target_file,
                'instruction': instruction,
                'chunks_analyzed': len(all_chunks),
                'detected_file': detection_info['file_path'] if detection_info else None,
                'detection_confidence': detection_info['confidence'] if detection_info else None
            }
            
            if save_local and self.enable_local_save:
                try:
                    local_path = self.doc_manager.save_edited_code(
                        code_content, target_file, repo_path, instruction
                    )
                    result['local_file'] = local_path
                except Exception as e:
                    print(f"⚠️  Failed to save locally: {e}")
            
            if push_to_github and self.enable_github and self.github_client:
                print(f"\n📤 Pushing edited code to GitHub...")
                clean_repo_path = repo_path.replace('repos/', '')
                
                try:
                    github_result = self.github_client.create_branch_and_push_code(
                        repo_path=clean_repo_path,
                        file_path=target_file,
                        new_content=code_content,
                        instruction=instruction
                    )
                    result['github'] = github_result
                    
                    if github_result.get('success'):
                        print(f"✓ PR created: {github_result.get('pr_url')}")
                except Exception as e:
                    result['github_error'] = str(e)
            
            return result
    
    # ==================== HELPER METHODS ====================
    
    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract code content from markdown response.
        
        Looks for code blocks in markdown format and extracts the content.
        Falls back to returning the entire response if no code blocks found.
        
        Args:
            response: LLM response that may contain code blocks
            
        Returns:
            Extracted code content
        """
        # Pattern for ```language ... ```
        pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            # Return the first code block
            return matches[0].strip()
        else:
            # No code blocks found, return as is
            return response.strip()
    
    def _generate_with_llm(self, prompt: str, max_tokens: int = 2048,
                          temperature: float = 0.3, stream: bool = False):
        """
        Helper to generate with LLM directly (without context search).
        
        Args:
            prompt: The prompt to send to LLM
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            stream: Enable streaming
            
        Returns:
            Generated text or stream iterator
        """
        if stream:
            return self.llm.generate_stream(prompt, max_tokens=max_tokens, temperature=temperature)
        else:
            return self.llm.generate(prompt, max_tokens=max_tokens, temperature=temperature)