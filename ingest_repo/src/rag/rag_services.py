"""
RAG Services: Q&A, Documentation, Code Completion, Code Editing
WITH STREAMING SUPPORT
"""
from typing import List, Dict, Optional, Iterator
from .llm_client_gemini_api import GeminiClient
from .vector_search import VectorSearch


class RAGServices:
    """
    Complete RAG system with 4 core services + streaming variants
    """
    
    def __init__(self, project_id: str, bucket_processed: str):
        self.llm = GeminiClient(project_id)
        self.search = VectorSearch(project_id, bucket_processed)
        self.project_id = project_id
    
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
        print(f"❓ Q&A SERVICE{'(Streaming)' if stream else ''}")
        print(f"{'='*60}")
        print(f"Question: {question}")
        
        # Retrieve relevant chunks
        chunks = self.search.search(question, repo_path, top_k=8, filter_language=language)
        
        if not chunks:
            return {
                'answer': "I couldn't find relevant information in the codebase.",
                'sources': []
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
                'type': c['chunk_type']
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
            
            print(f"\n✓ Answer generated with {len(sources)} sources")
            
            return {
                'answer': answer,
                'sources': sources,
                'chunks_used': len(chunks)
            }
    
    # ==================== SERVICE 2: DOCUMENTATION ====================
    
    def generate_documentation(self, target: str, repo_path: str,
                              doc_type: str = 'api',
                              stream: bool = False) -> Dict:
        """
        Generate professional documentation
        
        Args:
            target: What to document
            repo_path: Repository path
            doc_type: Type of docs (api, user_guide, technical, readme)
            stream: Enable streaming response
            
        Returns:
            Generated documentation (or iterator if streaming)
        """
        print(f"\n{'='*60}")
        print(f"📝 DOCUMENTATION SERVICE {'(Streaming)' if stream else ''}")
        print(f"{'='*60}")
        print(f"Target: {target}")
        print(f"Type: {doc_type}")
        
        # Search for relevant code
        query = f"documentation for {target} functions classes methods"
        chunks = self.search.search(query, repo_path, top_k=10)
        
        if not chunks:
            return {'documentation': "No relevant code found to document."}
        
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
                'streaming': True
            }
        else:
            # Regular generation
            docs = self.llm.generate_with_context(
                full_query, chunks, system_prompt, temperature=0.3, max_tokens=8192
            )
            
            print(f"✓ Documentation generated ({len(docs)} chars)")
            
            return {
                'documentation': docs,
                'type': doc_type,
                'files_referenced': len(set(c['file_path'] for c in chunks))
            }
    
    # ==================== SERVICE 3: CODE COMPLETION ====================
    
    def complete_code(self, code_context: str, cursor_position: str,
                     repo_path: str, language: str = 'python',
                     stream: bool = False) -> Dict:
        """
        Intelligent code completion
        
        Args:
            code_context: Code before cursor
            cursor_position: Current file and position
            repo_path: Repository path
            language: Programming language
            stream: Enable streaming
            
        Returns:
            Code suggestions
        """
        print(f"\n{'='*60}")
        print(f"💻 CODE COMPLETION SERVICE {'(Streaming)' if stream else ''}")
        print(f"{'='*60}")
        
        # Search for similar code patterns
        query = f"{language} code similar to: {code_context[-200:]}"
        chunks = self.search.search(query, repo_path, top_k=5, filter_language=language)
        
        system_prompt = f"""You are an expert {language} code completion assistant.

Based on the code context and similar patterns in the codebase, suggest the most likely code completion.

Instructions:
- Provide ONLY the code completion (no explanations unless asked)
- Match the coding style from the codebase
- Use appropriate variable names and patterns
- Include type hints if the codebase uses them
- Be concise but complete
- Generate syntactically correct code
"""
        
        completion_query = f"Complete this {language} code:\n\n{code_context}\n\n# Complete from here:"
        
        if stream:
            return {
                'completion_stream': self.llm.generate_with_context_stream(
                    completion_query, chunks, system_prompt, temperature=0.3, max_tokens=2048
                ),
                'language': language,
                'streaming': True
            }
        else:
            completion = self.llm.generate_with_context(
                completion_query, chunks, system_prompt, temperature=0.3, max_tokens=2048
            )
            
            print(f"✓ Completion generated")
            
            return {
                'completion': completion,
                'language': language,
                'confidence': 'high' if len(chunks) >= 3 else 'medium'
            }
    
    # ==================== SERVICE 4: CODE EDITING ====================
    
    def edit_code(self, instruction: str, target_file: str, 
                  repo_path: str, stream: bool = False) -> Dict:
        """
        Edit existing code based on instructions
        
        Args:
            instruction: What to change
            target_file: File to edit
            repo_path: Repository path
            stream: Enable streaming
            
        Returns:
            Modified code with explanation
        """
        print(f"\n{'='*60}")
        print(f"✏️  CODE EDITING SERVICE {'(Streaming)' if stream else ''}")
        print(f"{'='*60}")
        print(f"Instruction: {instruction}")
        print(f"Target: {target_file}")
        
        # Search for the target file
        query = f"{target_file} {instruction}"
        chunks = self.search.search(query, repo_path, top_k=10)
        
        # Filter to get chunks from target file
        target_chunks = [c for c in chunks if target_file in c['file_path']]
        
        if not target_chunks:
            return {
                'error': f"File {target_file} not found in indexed code",
                'modified_code': None
            }
        
        # Get surrounding context
        other_chunks = [c for c in chunks if target_file not in c['file_path']][:3]
        all_chunks = target_chunks + other_chunks
        
        system_prompt = """You are an expert code editor.

Modify the code according to the instruction while:
- Maintaining the existing style and patterns
- Keeping backward compatibility when possible
- Adding appropriate error handling
- Including comments for significant changes
- Following best practices

Provide:
1. The complete modified code
2. A brief explanation of changes
3. Any breaking changes or considerations

Format the response as:
```[language]
# Modified code here
```

**EXPLANATION:**
Brief description of what was changed and why
"""
        
        edit_query = f"Edit instruction: {instruction}\n\nModify the code from {target_file} appropriately."
        
        if stream:
            return {
                'modified_code_stream': self.llm.generate_with_context_stream(
                    edit_query, all_chunks, system_prompt, temperature=0.4, max_tokens=6144
                ),
                'file': target_file,
                'instruction': instruction,
                'streaming': True
            }
        else:
            response = self.llm.generate_with_context(
                edit_query, all_chunks, system_prompt, temperature=0.4, max_tokens=6144
            )
            
            print(f"✓ Code edited")
            
            return {
                'modified_code': response,
                'file': target_file,
                'instruction': instruction,
                'chunks_analyzed': len(all_chunks)
            }