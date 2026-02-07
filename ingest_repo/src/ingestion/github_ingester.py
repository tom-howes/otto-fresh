"""
Production GitHub repository ingestion module
"""
import os
import base64
import json
from datetime import datetime
from typing import Optional, Dict, List
from google.cloud import storage
import requests


class GitHubIngester:
    """Ingest GitHub repositories into Cloud Storage"""
    
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
    
    def ingest_repository(self, repo_url: str, branch: Optional[str] = None) -> Dict:
        """
        Ingest a GitHub repository
        
        Args:
            repo_url: GitHub repo URL or 'owner/repo' format
            branch: Specific branch to ingest (optional, uses default if None)
            
        Returns:
            Metadata dictionary with ingestion results
        """
        # Parse repository URL
        owner, repo = self._parse_repo_url(repo_url)
        repo_path = f"{owner}/{repo}"
        
        print(f"📥 Ingesting repository: {repo_path}")
        
        # Get repository info
        repo_info = self._get_repo_info(owner, repo)
        
        # Use specified branch or default
        target_branch = branch or repo_info.get('default_branch', 'main')
        print(f"✓ Branch: {target_branch}")
        
        # Fetch repository tree
        tree = self._get_repo_tree(owner, repo, target_branch)
        
        # Filter for code files only
        code_files = self._filter_code_files(tree)
        
        print(f"📁 Found {len(code_files)} code files to process")
        
        # Process and upload files
        files_metadata = self._process_files(owner, repo, code_files, repo_path)
        
        # Create and save metadata
        metadata = {
            'repo': repo_path,
            'owner': owner,
            'name': repo,
            'branch': target_branch,
            'ingested_at': datetime.now().isoformat(),
            'total_files': len(files_metadata),
            'files': files_metadata,
            'repo_info': {
                'description': repo_info.get('description', ''),
                'language': repo_info.get('language', ''),
                'stars': repo_info.get('stargazers_count', 0),
                'url': repo_info.get('html_url', '')
            }
        }
        
        self._save_metadata(repo_path, metadata)
        
        print(f"✅ Successfully ingested {len(files_metadata)} files")
        
        return metadata
    
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
    
    def _get_repo_info(self, owner: str, repo: str) -> Dict:
        """Get repository information from GitHub API"""
        url = f'https://api.github.com/repos/{owner}/{repo}'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def _get_repo_tree(self, owner: str, repo: str, branch: str) -> List[Dict]:
        """Get repository file tree"""
        url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('tree', [])
    
    def _filter_code_files(self, tree: List[Dict]) -> List[Dict]:
        """Filter for code files only, excluding binaries and common non-code files"""
        # Extensions to include
        code_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sql',
            '.md', '.yaml', '.yml', '.json', '.xml', '.html', '.css', '.scss'
        }
        
        # Paths to exclude
        exclude_paths = {
            'node_modules', 'venv', 'env', '__pycache__', '.git',
            'dist', 'build', 'target', '.next', 'coverage', '.pytest_cache'
        }
        
        filtered = []
        for item in tree:
            if item['type'] != 'blob':
                continue
            
            path = item['path']
            
            # Skip excluded directories
            if any(excluded in path for excluded in exclude_paths):
                continue
            
            # Check extension
            ext = '.' + path.split('.')[-1] if '.' in path else ''
            if ext.lower() in code_extensions:
                filtered.append(item)
        
        return filtered
    
    def _process_files(self, owner: str, repo: str, files: List[Dict], repo_path: str) -> List[Dict]:
        """Process and upload files to Cloud Storage"""
        bucket = self.storage_client.bucket(self.bucket_name)
        files_metadata = []
        
        for idx, item in enumerate(files, 1):
            try:
                # Get file content
                content = self._get_file_content(owner, repo, item['path'])
                
                if content is None:
                    print(f"⚠️  Skipping binary file: {item['path']}")
                    continue
                
                # Upload to Cloud Storage
                blob_path = f"{repo_path}/{item['path']}"
                blob = bucket.blob(blob_path)
                blob.upload_from_string(content)
                
                files_metadata.append({
                    'path': item['path'],
                    'size': item['size'],
                    'blob_path': blob_path,
                    'language': self._detect_language(item['path']),
                    'sha': item.get('sha', '')
                })
                
                if idx % 20 == 0:
                    print(f"✓ Processed {idx}/{len(files)} files")
                    
            except Exception as e:
                print(f"⚠️  Error processing {item['path']}: {e}")
                continue
        
        return files_metadata
    
    def _get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Get file content from GitHub"""
        url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return None
        
        file_data = response.json()
        
        try:
            content = base64.b64decode(file_data['content']).decode('utf-8')
            return content
        except:
            return None
    
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
        print(f"📊 Metadata: gs://{self.bucket_name}/{repo_path}/metadata.json")