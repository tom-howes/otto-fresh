#!/usr/bin/env python3
"""
RAG CLI - Interactive interface with STREAMING support
"""
import os
import sys
import argparse
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rag.rag_services import RAGServices

load_dotenv()


def print_streaming_response(response_dict, service_type):
    """Handle streaming responses"""
    
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
        return False
    
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
    
    # Stream the response
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
    
    # Print sources if available
    if 'sources' in response_dict and response_dict['sources']:
        print(f"\n{'='*60}")
        print("SOURCES:")
        print(f"{'='*60}")
        for i, src in enumerate(response_dict['sources'], 1):
            print(f"{i}. {src['file']} (lines {src['lines']}) - {src['type']}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='RAG-based Code Assistant with Streaming')
    parser.add_argument('repo', help='Repository path (owner/repo)')
    parser.add_argument('--service', choices=['qa', 'doc', 'complete', 'edit'], 
                       default='qa', help='Service to use')
    parser.add_argument('--stream', action='store_true', help='Enable streaming output')
    
    # Service-specific arguments
    parser.add_argument('--question', help='Question for Q&A service')
    parser.add_argument('--target', help='Target for documentation')
    parser.add_argument('--doc-type', choices=['api', 'user_guide', 'technical', 'readme'],
                       default='api', help='Documentation type')
    parser.add_argument('--code', help='Code context for completion')
    parser.add_argument('--instruction', help='Edit instruction')
    parser.add_argument('--file', help='Target file for editing')
    parser.add_argument('--language', help='Programming language filter')
    
    parser.add_argument('--project-id', default=os.getenv('PROJECT_ID'))
    parser.add_argument('--bucket', default=os.getenv('BUCKET_PROCESSED'))
    
    args = parser.parse_args()
    
    if not args.project_id or not args.bucket:
        print("Error: PROJECT_ID and BUCKET_PROCESSED must be set")
        sys.exit(1)
    
    # Initialize RAG services
    print("🚀 Initializing RAG services...")
    try:
        rag = RAGServices(args.project_id, args.bucket)
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
            if not print_streaming_response(result, 'qa'):
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
                args.target, args.repo, args.doc_type, stream=args.stream
            )
            
            # Handle streaming or regular response
            if not print_streaming_response(result, 'doc'):
                print(f"\n{'='*60}")
                print(f"{args.doc_type.upper()} DOCUMENTATION:")
                print(f"{'='*60}")
                print(result['documentation'])
        
        elif args.service == 'complete':
            if not args.code:
                print("Error: --code required for completion service")
                sys.exit(1)
            
            result = rag.complete_code(
                args.code, "", args.repo, args.language or 'python', stream=args.stream
            )
            
            # Handle streaming or regular response
            if not print_streaming_response(result, 'complete'):
                print(f"\n{'='*60}")
                print("CODE COMPLETION:")
                print(f"{'='*60}")
                print(result['completion'])
        
        elif args.service == 'edit':
            if not args.instruction or not args.file:
                print("Error: --instruction and --file required for edit service")
                sys.exit(1)
            
            result = rag.edit_code(
                args.instruction, args.file, args.repo, stream=args.stream
            )
            
            # Handle streaming or regular response
            if not print_streaming_response(result, 'edit'):
                print(f"\n{'='*60}")
                print("EDITED CODE:")
                print(f"{'='*60}")
                print(result.get('modified_code', result.get('error', 'No changes')))
    
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