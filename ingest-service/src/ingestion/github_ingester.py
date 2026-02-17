"""
Production GitHub repository ingestion with multi-user support
Features: Shared storage, commit tracking, smart caching
"""
import os
import base64
import json
from datetime import datetime
from typing import Optional, Dict, List
from google.cloud import storage
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time


class GitHubIngester:
    """
    Ingest GitHub repositories with shared storage
    
    Multiple users can ingest the same repo - chunks stored once and shared
    """
    
    def __init__(self, project_id: str, bucket_name: str, github_token: Optional[str] = None):
        """
        Initialize the ingester
        
        Args:
            project_id: GCP project ID
            bucket_name: Cloud Storage bucket for raw files
            github_token: GitHub personal access token (optional)
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.github_token = github_token
        self.storage_client = storage.Client(project=project_id)
        
        self.headers = {}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
        
        self.session = self._create_retry_session()
    
    def _create_retry_session(self, retries: int = 3) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _make_github_request(self, url: str, max_retries: int = 3) -> Dict:
        """Make GitHub API request with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.SSLError as e:
                print(f"⚠️  SSL Error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            
            except requests.exceptions.ConnectionError as e:
                print(f"⚠️  Connection Error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            
            except requests.exceptions.RequestException as e:
                print(f"❌ Request Error: {e}")
                raise
    
    def ingest_repository(self, repo_url: str, branch: Optional[str] = None) -> Dict:
        """
        Ingest a GitHub repository into SHARED storage
        
        Features:
        - Shared storage (one copy per repo, not per user)
        - Commit tracking for incremental updates
        - Full metadata capture
        
        Args:
            repo_url: GitHub repo URL or 'owner/repo' format
            branch: Specific branch to ingest (optional)
            
        Returns:
            Metadata dictionary with ingestion results
        """
        # Parse repository URL
        owner, repo = self._parse_repo_url(repo_url)
        repo_full_name = f"{owner}/{repo}"
        
        # ALWAYS use shared path (not user-specific)
        from src.utils.storage_utils import get_shared_repo_path
        repo_path = get_shared_repo_path(repo_full_name)
        
        print(f"\n{'='*60}")
        print(f"📥 INGESTING REPOSITORY")
        print(f"{'='*60}")
        print(f"Repository: {repo_full_name}")
        print(f"Storage path: {repo_path}")
        print(f"Storage type: Shared (multi-user)")
        print(f"{'='*60}\n")
        
        try:
            # Get repository info
            repo_url_api = f'https://api.github.com/repos/{repo_full_name}'
            repo_info = self._make_github_request(repo_url_api)
            
            # Use specified branch or default
            target_branch = branch or repo_info.get('default_branch', 'main')
            print(f"✓ Branch: {target_branch}")
            
            # Get current commit SHA (for tracking)
            branch_url = f'https://api.github.com/repos/{repo_full_name}/branches/{target_branch}'
            branch_info = self._make_github_request(branch_url)
            current_commit_sha = branch_info['commit']['sha']
            current_commit_author = branch_info['commit']['commit']['author']['name']
            current_commit_message = branch_info['commit']['commit']['message'].split('\n')[0]
            
            print(f"✓ Current commit: {current_commit_sha[:8]}")
            print(f"   Author: {current_commit_author}")
            print(f"   Message: {current_commit_message[:60]}")
            
            # Fetch repository tree
            tree_url = f'https://api.github.com/repos/{repo_full_name}/git/trees/{target_branch}?recursive=1'
            tree_response = self._make_github_request(tree_url)
            tree = tree_response.get('tree', [])
            
            # Filter for code files
            code_files = self._filter_code_files(tree)
            print(f"📁 Found {len(code_files)} code files to process")
            
            # Process and upload files
            files_metadata = self._process_files(owner, repo, code_files, repo_path, target_branch)
            
            # Create comprehensive metadata
            metadata = {
                'repo': repo_path,
                'repo_full_name': repo_full_name,
                'owner': owner,
                'name': repo,
                'branch': target_branch,
                'commit_sha': current_commit_sha,
                'commit_author': current_commit_author,
                'commit_message': current_commit_message,
                'ingested_at': datetime.now().isoformat(),
                'total_files': len(files_metadata),
                'files': files_metadata,
                'repo_info': {
                    'description': repo_info.get('description', ''),
                    'language': repo_info.get('language', ''),
                    'stars': repo_info.get('stargazers_count', 0),
                    'url': repo_info.get('html_url', ''),
                    'private': repo_info.get('private', False)
                },
                'storage_type': 'shared'
            }
            
            self._save_metadata(repo_path, metadata)
            
            print(f"\n{'='*60}")
            print(f"✅ INGESTION COMPLETE")
            print(f"{'='*60}")
            print(f"Repository: {repo_full_name}")
            print(f"Files: {len(files_metadata)}")
            print(f"Commit: {current_commit_sha[:8]}")
            print(f"Storage: gs://{self.bucket_name}/{repo_path}/")
            print(f"{'='*60}\n")
            
            return metadata
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to ingest repository: {e}")
            print("\nTroubleshooting:")
            print("1. Check your internet connection")
            print("2. Verify GitHub token is valid")
            print("3. Check if repository exists and is accessible")
            raise
    
    def _parse_repo_url(self, repo_url: str) -> tuple:
        """Parse GitHub repo URL into owner and repo name"""
        if 'github.com' in repo_url:
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]
            if repo.endswith('.git'):
                repo = repo[:-4]
        else:
            owner, repo = repo_url.split('/')
        return owner, repo
    
    def _filter_code_files(self, tree: List[Dict]) -> List[Dict]:
        """Filter for code files only"""
        code_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sql',
            '.md', '.yaml', '.yml', '.json', '.xml', '.html', '.css', '.scss'
        }
        
        exclude_paths = {
            'node_modules', 'venv', 'env', '__pycache__', '.git',
            'dist', 'build', 'target', '.next', 'coverage', '.pytest_cache'
        }
        
        filtered = []
        for item in tree:
            if item['type'] != 'blob':
                continue
            
            path = item['path']
            
            if any(excluded in path for excluded in exclude_paths):
                continue
            
            ext = '.' + path.split('.')[-1] if '.' in path else ''
            if ext.lower() in code_extensions:
                filtered.append(item)
        
        return filtered
    
    def _process_files(self, owner: str, repo: str, files: List[Dict], 
                      repo_path: str, branch: str) -> List[Dict]:
        """Process and upload files using PyGithub"""
        from github import Github
        
        print(f"Initializing GitHub client...")
        github_client = Github(self.github_token) if self.github_token else Github()
        
        try:
            gh_repo = github_client.get_repo(f"{owner}/{repo}")
            print(f"✓ Connected to repo, using branch: {branch}")
        except Exception as e:
            print(f"❌ Failed to connect to repo: {e}")
            raise
        
        bucket = self.storage_client.bucket(self.bucket_name)
        files_metadata = []
        skipped = 0
        
        print(f"\nProcessing {len(files)} files from branch '{branch}'...")
        
        for idx, item in enumerate(files, 1):
            try:
                file_path = item['path']
                
                # Get file content from SPECIFIED BRANCH
                try:
                    file_content = gh_repo.get_contents(file_path, ref=branch)
                except Exception as e:
                    print(f"⚠️  Could not fetch {file_path}: {str(e)[:60]}")
                    skipped += 1
                    continue
                
                if file_content.type != 'file':
                    continue
                
                # Decode content
                try:
                    content = file_content.decoded_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content = file_content.decoded_content.decode('utf-8', errors='ignore')
                    except Exception:
                        skipped += 1
                        continue
                
                if not content or len(content.strip()) == 0:
                    skipped += 1
                    continue
                
                if '\x00' in content:
                    skipped += 1
                    continue
                
                # Upload to Cloud Storage
                blob_path = f"{repo_path}/{file_path}"
                blob = bucket.blob(blob_path)
                blob.upload_from_string(content)
                
                files_metadata.append({
                    'path': file_path,
                    'size': len(content),
                    'blob_path': blob_path,
                    'language': self._detect_language(file_path),
                    'sha': file_content.sha
                })
                
                if idx % 10 == 0 or idx == len(files):
                    print(f"✓ Processed {idx}/{len(files)} files ({len(files_metadata)} successful, {skipped} skipped)")
                    
            except Exception as e:
                print(f"⚠️  Error processing {item['path']}: {str(e)[:100]}")
                skipped += 1
                continue
        
        print(f"\n✅ Processing summary:")
        print(f"   Total: {len(files)}")
        print(f"   Success: {len(files_metadata)}")
        print(f"   Skipped: {skipped}")
        
        return files_metadata
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        extensions = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.tsx': 'typescript', '.jsx': 'javascript', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.h': 'c', '.go': 'go',
            '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.swift': 'swift',
            '.kt': 'kotlin', '.scala': 'scala', '.sql': 'sql',
            '.md': 'markdown', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
            '.html': 'html', '.css': 'css', '.scss': 'scss'
        }
        
        ext = '.' + file_path.split('.')[-1] if '.' in file_path else ''
        return extensions.get(ext.lower(), 'unknown')
    
    def _save_metadata(self, repo_path: str, metadata: Dict):
        """Save metadata to Cloud Storage"""
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(f"{repo_path}/metadata.json")
        blob.upload_from_string(json.dumps(metadata, indent=2))
        print(f"📊 Metadata saved: gs://{self.bucket_name}/{repo_path}/metadata.json")