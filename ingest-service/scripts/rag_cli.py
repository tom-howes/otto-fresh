#!/usr/bin/env python3
"""
RAG CLI - Interactive interface with STREAMING support + GitHub Integration
"""
import os
import sys
import argparse
from dotenv import load_dotenv
import config

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rag.rag_services import RAGServices

load_dotenv()


def print_streaming_response(response_dict, service_type):
    """Handle streaming responses and capture output"""
    
    # Determine which stream key to use
    stream_key_map = {
        'qa': 'answer_stream',
        'doc': 'documentation_stream',
        'complete': 'completion_stream',
        'edit': 'modified_code_stream'
    }
    
    stream_key = stream_key_map.get(service_type)
    
    if not stream_key or stream_key not in response_dict:
        # Not a streaming response
        return False, None
    
    print(f"\n{'='*60}")
    
    if service_type == 'qa':
        print("ANSWER:")
    elif service_type == 'doc':
        print(f"{response_dict.get('type', 'DOCUMENTATION').upper()}:")
    elif service_type == 'complete':
        print("CODE COMPLETION:")
    elif service_type == 'edit':
        print("EDITED CODE:")
    
    print(f"{'='*60}\n")
    
    # Stream the response and CAPTURE it
    full_response = []
    try:
        for chunk in response_dict[stream_key]:
            print(chunk, end='', flush=True)
            full_response.append(chunk)
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
    except Exception as e:
        print(f"\n\n⚠️  Streaming error: {e}")
    
    print("\n")
    
    # Combine all chunks into complete response
    complete_response = ''.join(full_response)
    
    # Print sources if available
    if 'sources' in response_dict and response_dict['sources']:
        print(f"\n{'='*60}")
        print("SOURCES:")
        print(f"{'='*60}")
        for i, src in enumerate(response_dict['sources'], 1):
            print(f"{i}. {src['file']} (lines {src['lines']}) - {src['type']}")
    
    return True, complete_response  # Return captured content


def main():
    parser = argparse.ArgumentParser(description='RAG-based Code Assistant with GitHub Integration')
    parser.add_argument('repo', help='Repository path (owner/repo)')
    parser.add_argument('--service', choices=['qa', 'doc', 'complete', 'edit'], 
                       default='qa', help='Service to use')
    parser.add_argument('--stream', action='store_true', help='Enable streaming output')
    
    # GitHub integration flags
    parser.add_argument('--push', action='store_true', 
                       help='Push changes/docs to GitHub (creates PR)')
    parser.add_argument('--no-local', action='store_true',
                       help='Skip saving files locally')
    
    # Service-specific arguments
    parser.add_argument('--question', help='Question for Q&A service')
    parser.add_argument('--target', help='Target for documentation')
    parser.add_argument('--doc-type', choices=['api', 'user_guide', 'technical', 'readme'],
                       default='api', help='Documentation type')
    parser.add_argument('--code', help='Code context for completion')
    parser.add_argument('--instruction', help='Edit instruction')
    parser.add_argument('--file', help='Target file for editing/completion')
    parser.add_argument('--language', help='Programming language filter')
    
    parser.add_argument('--project-id', default=config.getenv('PROJECT_ID'))
    parser.add_argument('--bucket', default=config.getenv('BUCKET_PROCESSED'))
    
    args = parser.parse_args()
    
    if not args.project_id or not args.bucket:
        print("Error: PROJECT_ID and BUCKET_PROCESSED must be set")
        sys.exit(1)
    
    # Initialize RAG services with GitHub
    print("🚀 Initializing RAG services...")
    try:
        rag = RAGServices(
            args.project_id, 
            args.bucket,
            enable_github=True,
            enable_local_save=not args.no_local
        )
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        sys.exit(1)
    
    # Route to appropriate service
    try:
        if args.service == 'qa':
            if not args.question:
                print("Error: --question required for Q&A service")
                sys.exit(1)
            
            result = rag.answer_question(
                args.question, args.repo, args.language, stream=args.stream
            )
            
            # Handle streaming or regular response
            was_streaming, captured_response = print_streaming_response(result, 'qa')
            
            if not was_streaming:
                print(f"\n{'='*60}")
                print("ANSWER:")
                print(f"{'='*60}")
                print(result['answer'])
                
                if result.get('sources'):
                    print(f"\n{'='*60}")
                    print("SOURCES:")
                    print(f"{'='*60}")
                    for i, src in enumerate(result['sources'], 1):
                        print(f"{i}. {src['file']} (lines {src['lines']}) - {src['type']}")
        
        elif args.service == 'doc':
            if not args.target:
                print("Error: --target required for documentation service")
                sys.exit(1)
            
            result = rag.generate_documentation(
                args.target, args.repo, args.doc_type, 
                stream=args.stream,
                push_to_github=args.push if not args.stream else False,  # Push after streaming
                save_local=(not args.no_local) if not args.stream else False  # Save after streaming
            )
            
            # Handle streaming or regular response
            was_streaming, captured_response = print_streaming_response(result, 'doc')
            
            if was_streaming and captured_response:
                # POST-PROCESSING: Save and push the captured streaming response
                print(f"\n{'='*60}")
                print("POST-PROCESSING STREAMING OUTPUT")
                print(f"{'='*60}")
                print(f"Captured: {len(captured_response)} characters")
                
                # Save locally
                if not args.no_local:
                    print("\n💾 Saving documentation locally...")
                    try:
                        local_path = rag.doc_manager.save_documentation(
                            captured_response, args.target, args.doc_type, args.repo
                        )
                        print(f"✓ Saved to: {local_path}")
                    except Exception as e:
                        print(f"❌ Failed to save locally: {e}")
                
                # Push to GitHub
                if args.push:
                    print("\n📤 Pushing to GitHub...")
                    try:
                        github_result = rag.github_client.push_documentation(
                            args.repo, captured_response, args.target, args.doc_type, create_pr=True
                        )
                        
                        if github_result.get('success'):
                            if github_result.get('pr_url'):
                                print(f"✓ Pull request created: {github_result['pr_url']}")
                            print(f"✓ Branch: {github_result.get('branch', 'N/A')}")
                            print(f"✓ File: {github_result.get('file_path', 'N/A')}")
                        else:
                            print(f"❌ GitHub push failed: {github_result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"❌ Failed to push to GitHub: {e}")
                
            elif not was_streaming:
                # Regular response (non-streaming)
                print(f"\n{'='*60}")
                print(f"{args.doc_type.upper()} DOCUMENTATION:")
                print(f"{'='*60}")
                print(result['documentation'])
                
                if result.get('local_file'):
                    print(f"\n📁 Saved locally: {result['local_file']}")
                
                if result.get('github', {}).get('pr_url'):
                    print(f"\n🔗 GitHub PR: {result['github']['pr_url']}")
                    print(f"🌿 Branch: {result['github'].get('branch', 'N/A')}")
        
        elif args.service == 'complete':
            if not args.code:
                print("Error: --code required for completion service")
                sys.exit(1)
            
            result = rag.complete_code(
                args.code, "", args.repo, args.language or 'python',
                stream=args.stream,
                push_to_github=args.push if not args.stream else False,
                save_local=(not args.no_local) if not args.stream else False,
                target_file=args.file
            )
            
            # Handle streaming or regular response
            was_streaming, captured_response = print_streaming_response(result, 'complete')
            
            if was_streaming and captured_response:
                # POST-PROCESSING
                print(f"\n{'='*60}")
                print("POST-PROCESSING STREAMING OUTPUT")
                print(f"{'='*60}")
                
                # Extract code from response
                code_content = rag._extract_code_from_response(captured_response)
                
                # Combine with original context
                full_code = result.get('code_context', args.code) + "\n" + code_content
                
                # Save locally
                if not args.no_local and args.file:
                    print("\n💾 Saving completed code locally...")
                    try:
                        local_path = rag.doc_manager.save_edited_code(
                            full_code, args.file, args.repo, "AI code completion"
                        )
                        print(f"✓ Saved to: {local_path}")
                    except Exception as e:
                        print(f"❌ Failed to save locally: {e}")
                
                # Push to GitHub
                if args.push and args.file:
                    print("\n📤 Pushing to GitHub...")
                    try:
                        github_result = rag.github_client.create_branch_and_push_code(
                            args.repo, args.file, full_code, "AI code completion"
                        )
                        
                        if github_result.get('success'):
                            print(f"✓ Branch created: {github_result['branch']}")
                            if github_result.get('pr_url'):
                                print(f"✓ Pull request created: {github_result['pr_url']}")
                        else:
                            print(f"❌ GitHub push failed: {github_result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"❌ Failed to push to GitHub: {e}")
                elif args.push and not args.file:
                    print("\n⚠️  --file required for GitHub push")
            
            elif not was_streaming:
                # Regular response
                print(f"\n{'='*60}")
                print("CODE COMPLETION:")
                print(f"{'='*60}")
                print(result['completion'])
                
                if result.get('local_file'):
                    print(f"\n📁 Saved locally: {result['local_file']}")
                
                if result.get('github', {}).get('pr_url'):
                    print(f"\n🔗 GitHub PR: {result['github']['pr_url']}")
                    print(f"🌿 Branch: {result['github']['branch']}")
        
        elif args.service == 'edit':
            if not args.instruction or not args.file:
                print("Error: --instruction and --file required for edit service")
                sys.exit(1)
            
            result = rag.edit_code(
                args.instruction, args.file, args.repo,
                stream=args.stream,
                push_to_github=args.push if not args.stream else False,
                save_local=(not args.no_local) if not args.stream else False
            )
            
            # Handle streaming or regular response
            was_streaming, captured_response = print_streaming_response(result, 'edit')
            
            if was_streaming and captured_response:
                # POST-PROCESSING
                print(f"\n{'='*60}")
                print("POST-PROCESSING STREAMING OUTPUT")
                print(f"{'='*60}")
                print(f"Captured: {len(captured_response)} characters")
                
                # Extract code from response
                code_content = rag._extract_code_from_response(captured_response)
                
                # Save locally
                if not args.no_local:
                    print("\n💾 Saving edited code locally...")
                    try:
                        local_path = rag.doc_manager.save_edited_code(
                            code_content, args.file, args.repo, args.instruction
                        )
                        print(f"✓ Saved to: {local_path}")
                    except Exception as e:
                        print(f"❌ Failed to save locally: {e}")
                
                # Push to GitHub
                if args.push:
                    print("\n📤 Pushing to GitHub...")
                    try:
                        github_result = rag.github_client.create_branch_and_push_code(
                            args.repo, args.file, code_content, args.instruction
                        )
                        
                        if github_result.get('success'):
                            print(f"✓ Branch created: {github_result['branch']}")
                            if github_result.get('pr_url'):
                                print(f"✓ Pull request created: {github_result['pr_url']}")
                        else:
                            print(f"❌ GitHub push failed: {github_result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"❌ Failed to push to GitHub: {e}")
                
            elif not was_streaming:
                # Regular response
                print(f"\n{'='*60}")
                print("EDITED CODE:")
                print(f"{'='*60}")
                print(result.get('modified_code', result.get('error', 'No changes')))
                
                if result.get('local_file'):
                    print(f"\n📁 Saved locally: {result['local_file']}")
                
                if result.get('github', {}).get('pr_url'):
                    print(f"\n🔗 GitHub PR: {result['github']['pr_url']}")
                    print(f"🌿 Branch: {result['github']['branch']}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()