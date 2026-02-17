# ingest-service/src/rag/rag_services.py
"""
RAG Services: Q&A, Documentation, Code Completion, Code Editing
WITH STREAMING SUPPORT + GitHub Integration + Local Save
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
    Complete RAG system with 4 core services + streaming variants + GitHub integration
    """
    
    def __init__(self, project_id: str, bucket_processed: str,
                 enable_github: bool = True, enable_local_save: bool = True):
        """
        Initialize RAG services
        
        Args:
            project_id: GCP project ID
            bucket_processed: Bucket with processed chunks
            enable_github: Enable GitHub integration
            enable_local_save: Enable local file saving
        """
        self.llm = GeminiClient(project_id)
        self.search = VectorSearch(project_id, bucket_processed)
        self.project_id = project_id
        self.bucket_name = bucket_processed
        
        # GitHub integration
        self.enable_github = enable_github
        self.github_client = None  # Set externally with user's token
        
        # Local file management
        self.enable_local_save = enable_local_save
        if enable_local_save:
            self.doc_manager = DocumentationManager()
    
    # ==================== SERVICE 1: Q&A ====================
    
    def answer_question(self, question: str, repo_path: str, 
                       language: Optional[str] = None,
                       stream: bool = False) -> Dict:
        """
        Answer questions about the codebase
        
        Args:
            question: User's question
            repo_path: Repository path
            language: Optional language filter
            stream: Enable streaming response
            
        Returns:
            Answer with sources (or iterator if streaming)
        """
        print(f"\n{'='*60}")
        print(f"❓ Q&A SERVICE {('(Streaming)' if stream else '')}")
        print(f"{'='*60}")
        print(f"Question: {question}")
        
        # Retrieve relevant chunks
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
        
        # Extract sources
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
            # Return iterator for streaming
            return {
                'answer_stream': self.llm.generate_with_context_stream(
                    question, chunks, system_prompt, temperature=0.2, max_tokens=4096
                ),
                'sources': sources,
                'streaming': True
            }
        else:
            # Regular generation
            answer = self.llm.generate_with_context(
                question, chunks, system_prompt, temperature=0.2, max_tokens=4096
            )
            
            print(f"✓ Answer generated with {len(sources)} sources")
            
            return {
                'answer': answer,
                'sources': sources,
                'chunks_used': len(chunks)
            }
    
    # ==================== SERVICE 2: DOCUMENTATION ====================
    
    def generate_documentation(self, target: str, repo_path: str,
                              doc_type: str = 'api',
                              stream: bool = False,
                              push_to_github: bool = False,
                              save_local: bool = True) -> Dict:
        """
        Generate professional documentation
        
        Args:
            target: What to document
            repo_path: Repository path
            doc_type: Type of docs (api, user_guide, technical, readme)
            stream: Enable streaming response
            push_to_github: Push to GitHub repo
            save_local: Save locally as .md file
            
        Returns:
            Generated documentation with file paths
        """
        print(f"\n{'='*60}")
        print(f"📝 DOCUMENTATION SERVICE {('(Streaming)' if stream else '')}")
        print(f"{'='*60}")
        print(f"Target: {target}")
        print(f"Type: {doc_type}")
        
        # Search for relevant code
        query = f"documentation for {target} functions classes methods"
        chunks = self.search.search(query, repo_path, top_k=10)
        
        if not chunks:
            return {
                'documentation': "No relevant code found to document.",
                'type': doc_type,
                'files_referenced': 0
            }
        
        # System prompts for different doc types
        prompts = {
            'api': """Generate comprehensive API documentation in Markdown format.

Include:
1. **Overview and Purpose** - What this API does
2. **Functions/Classes** - Full signatures with all parameters
3. **Parameters** - Type, description, required/optional for each
4. **Return Values** - Types and descriptions
5. **Usage Examples** - Practical code examples
6. **Error Handling** - What exceptions can be raised
7. **Common Use Cases** - Real-world scenarios

Be thorough and complete. Generate FULL documentation, not summaries.""",
            
            'user_guide': """Generate a comprehensive user guide in Markdown format.

Include:
1. **Introduction** - Clear overview
2. **Getting Started** - Prerequisites and setup
3. **Step-by-Step Instructions** - Detailed walkthrough
4. **Common Use Cases** - Practical examples
5. **Troubleshooting** - Common issues and solutions
6. **Best Practices** - Tips and recommendations
7. **FAQ** - Frequently asked questions

Be detailed and user-friendly.""",
            
            'technical': """Generate detailed technical documentation in Markdown format.

Include:
1. **Architecture Overview** - System design
2. **Implementation Details** - How it works internally
3. **Design Patterns** - Patterns used and why
4. **Dependencies** - External libraries and services
5. **Performance Considerations** - Optimization details
6. **Code Examples** - Detailed implementation examples
7. **Technical Constraints** - Limitations and trade-offs

Be thorough and technical.""",
            
            'readme': """Generate a comprehensive README.md.

Include:
1. **Project Title and Description**
2. **Features** - Key capabilities
3. **Installation** - Step-by-step setup
4. **Usage** - Quick start examples
5. **API Reference** - Key functions/classes
6. **Configuration** - Environment variables, settings
7. **Contributing** - How to contribute
8. **License** - Project license

Be complete and professional."""
        }
        
        system_prompt = prompts.get(doc_type, prompts['api'])
        
        full_query = f"""Generate COMPLETE {doc_type} documentation for: {target}

IMPORTANT: 
- Provide a COMPREHENSIVE, DETAILED response
- Cover ALL aspects mentioned in the instructions
- Do NOT truncate or summarize
- Include ALL code examples and details
- Generate the FULL documentation"""
        
        if stream:
            # Return streaming response
            return {
                'documentation_stream': self.llm.generate_with_context_stream(
                    full_query, chunks, system_prompt, temperature=0.3, max_tokens=8192
                ),
                'type': doc_type,
                'files_referenced': len(set(c['file_path'] for c in chunks)),
                'streaming': True,
                'repo_path': repo_path,
                'target': target
            }
        else:
            # Regular generation
            docs = self.llm.generate_with_context(
                full_query, chunks, system_prompt, temperature=0.3, max_tokens=8192
            )
            
            print(f"✓ Documentation generated ({len(docs)} chars)")
            
            result = {
                'documentation': docs,
                'type': doc_type,
                'files_referenced': len(set(c['file_path'] for c in chunks))
            }
            
            # Save locally
            if save_local and self.enable_local_save:
                local_path = self.doc_manager.save_documentation(
                    docs, target, doc_type, repo_path
                )
                result['local_file'] = local_path
                print(f"✓ Saved locally: {local_path}")
            
            # Push to GitHub
            if push_to_github and self.enable_github and self.github_client:
                print("\n📤 Pushing documentation to GitHub...")
                
                # Clean repo path
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
    
    # ==================== SERVICE 3: CODE COMPLETION ====================
    
    def complete_code(self, code_context: str, cursor_position: str,
                     repo_path: str, language: str = 'python',
                     stream: bool = False,
                     push_to_github: bool = False,
                     save_local: bool = False,
                     target_file: Optional[str] = None) -> Dict:
        """
        Intelligent code completion
        
        Args:
            code_context: Code before cursor
            cursor_position: Current file and position
            repo_path: Repository path
            language: Programming language
            stream: Enable streaming
            push_to_github: Push completed code to GitHub (requires target_file)
            save_local: Save completed code locally
            target_file: File being edited (REQUIRED if push_to_github=True)
            
        Returns:
            Code suggestions with optional save/push
        """
        print(f"\n{'='*60}")
        print(f"💻 CODE COMPLETION SERVICE {('(Streaming)' if stream else '')}")
        print(f"{'='*60}")
        print(f"Language: {language}")
        print(f"Context length: {len(code_context)} chars")
        print(f"Push to GitHub: {push_to_github}")
        print(f"Target file: {target_file}")
        
        # Search for similar code patterns
        query = f"{language} code similar to: {code_context[-200:]}"
        chunks = self.search.search(query, repo_path, top_k=5, filter_language=language)
        
        # Build context from similar chunks
        context_parts = []
        for chunk in chunks:
            context_parts.append(f"# Similar pattern from {chunk['file_path']}:\n{chunk['content'][:300]}")
        
        context = "\n\n".join(context_parts)
        
        system_prompt = f"""You are an expert {language} code completion assistant.

Based on the code context and similar patterns in the codebase, suggest the most likely code completion.

Instructions:
- Provide ONLY the code completion (no explanations)
- Match the coding style from the codebase
- Use appropriate variable names and patterns
- Include type hints if the codebase uses them
- Be concise but complete
- Generate syntactically correct code
"""
        
        completion_query = f"""Complete this {language} code:
```{language}
{code_context}
```

Repository patterns:
{context}

Provide ONLY the code completion (next lines), no explanations.
"""
        
        if stream:
            return {
                'completion_stream': self.llm.generate_with_context_stream(
                    completion_query, chunks, system_prompt, temperature=0.3, max_tokens=1024
                ),
                'language': language,
                'streaming': True,
                'repo_path': repo_path,
                'target_file': target_file
            }
        else:
            completion = self.llm.generate_with_context(
                completion_query, chunks, system_prompt, temperature=0.3, max_tokens=1024
            )
            
            print(f"✓ Completion generated ({len(completion)} chars)")
            
            # Extract code from response
            code_content = self._extract_code_from_response(completion)
            
            # Combine with original context to create full file content
            full_code = code_context + "\n" + code_content
            
            result = {
                'completion': completion,
                'language': language,
                'confidence': 'high' if len(chunks) >= 3 else 'medium',
                'patterns_found': len(chunks)
            }
            
            # Push to GitHub if requested
            if push_to_github and self.enable_github and self.github_client:
                if not target_file:
                    result['github_error'] = "target_file is required when push_to_github=true"
                    print("❌ Cannot push to GitHub: target_file not specified")
                else:
                    print(f"\n📤 Pushing code completion to GitHub...")
                    print(f"   File: {target_file}")
                    
                    # Clean repo path
                    clean_repo_path = repo_path.replace('repos/', '')
                    
                    github_result = self.github_client.create_branch_and_push_code(
                        repo_path=clean_repo_path,
                        file_path=target_file,
                        new_content=full_code,
                        instruction=f"AI code completion: {code_context[:60]}..."
                    )
                    result['github'] = github_result
                    
                    if github_result.get('success'):
                        print(f"✓ Branch created: {github_result['branch']}")
                        if github_result.get('pr_url'):
                            print(f"✓ Pull request: {github_result['pr_url']}")
                    else:
                        print(f"❌ GitHub push failed: {github_result.get('error')}")
            
            # Save locally
            if save_local and self.enable_local_save and target_file:
                local_path = self.doc_manager.save_edited_code(
                    full_code, target_file, repo_path, "code completion"
                )
                result['local_file'] = local_path
                print(f"✓ Saved locally: {local_path}")
            
            return result
    
    # ==================== SERVICE 4: CODE EDITING ====================
    
    def edit_code(self, instruction: str, target_file: str, 
                  repo_path: str, stream: bool = False,
                  push_to_github: bool = False,
                  save_local: bool = True) -> Dict:
        """
        Edit existing code based on natural language instructions
        
        Args:
            instruction: What to change (natural language)
            target_file: File to edit
            repo_path: Repository path
            stream: Enable streaming
            push_to_github: Create PR with changes
            save_local: Save edited code locally
            
        Returns:
            Modified code with optional save/push
        """
        print(f"\n{'='*60}")
        print(f"✏️  CODE EDITING SERVICE {('(Streaming)' if stream else '')}")
        print(f"{'='*60}")
        print(f"Instruction: {instruction}")
        print(f"Target: {target_file}")
        print(f"Push to GitHub: {push_to_github}")
        
        # Search for the target file
        query = f"{target_file} {instruction}"
        chunks = self.search.search(query, repo_path, top_k=10)
        
        # Filter to get chunks from target file
        target_chunks = [c for c in chunks if target_file in c['file_path']]
        
        if not target_chunks:
            return {
                'error': f"File {target_file} not found in indexed code",
                'modified_code': None,
                'file': target_file,
                'instruction': instruction,
                'chunks_analyzed': 0
            }
        
        # Get surrounding context
        other_chunks = [c for c in chunks if target_file not in c['file_path']][:3]
        all_chunks = target_chunks + other_chunks
        
        print(f"✓ Found {len(target_chunks)} chunks from {target_file}")
        print(f"✓ Added {len(other_chunks)} chunks for context")
        
        system_prompt = """You are an expert code editor.

Modify the code according to the instruction while:
- Maintaining the existing style and patterns
- Keeping backward compatibility when possible
- Adding appropriate error handling
- Including comments for significant changes
- Following best practices

Provide the complete modified code in a code block.

Format:
```[language]
# Complete modified code here
```

Then briefly explain what was changed.
"""
        
        edit_query = f"""Edit instruction: {instruction}

Modify the code from {target_file} according to the instruction above.
Provide the COMPLETE modified file content.
"""
        
        if stream:
            return {
                'modified_code_stream': self.llm.generate_with_context_stream(
                    edit_query, all_chunks, system_prompt, temperature=0.4, max_tokens=6144
                ),
                'file': target_file,
                'instruction': instruction,
                'streaming': True,
                'repo_path': repo_path
            }
        else:
            response = self.llm.generate_with_context(
                edit_query, all_chunks, system_prompt, temperature=0.4, max_tokens=6144
            )
            
            print(f"✓ Code edited ({len(response)} chars)")
            
            # Extract code from response
            code_content = self._extract_code_from_response(response)
            
            result = {
                'modified_code': response,
                'file': target_file,
                'instruction': instruction,
                'chunks_analyzed': len(all_chunks)
            }
            
            # Save locally
            if save_local and self.enable_local_save:
                local_path = self.doc_manager.save_edited_code(
                    code_content, target_file, repo_path, instruction
                )
                result['local_file'] = local_path
                print(f"✓ Saved locally: {local_path}")
            
            # Push to GitHub
            if push_to_github and self.enable_github and self.github_client:
                print(f"\n📤 Pushing edited code to GitHub...")
                
                # Clean repo path (remove 'repos/' prefix if present)
                clean_repo_path = repo_path.replace('repos/', '')
                
                github_result = self.github_client.create_branch_and_push_code(
                    repo_path=clean_repo_path,
                    file_path=target_file,
                    new_content=code_content,
                    instruction=instruction
                )
                result['github'] = github_result
                
                if github_result.get('success'):
                    print(f"✓ Branch created: {github_result['branch']}")
                    if github_result.get('pr_url'):
                        print(f"✓ Pull request created: {github_result['pr_url']}")
                else:
                    print(f"❌ GitHub push failed: {github_result.get('error')}")
            
            return result
    
    # ==================== HELPER METHODS ====================
    
    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract code content from markdown response
        
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
        Helper to generate with LLM directly (without context search)
        
        Args:
            prompt: The prompt to send to LLM
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Enable streaming
            
        Returns:
            Generated text or stream iterator
        """
        if stream:
            return self.llm.generate_stream(prompt, max_tokens=max_tokens, temperature=temperature)
        else:
            return self.llm.generate(prompt, max_tokens=max_tokens, temperature=temperature)