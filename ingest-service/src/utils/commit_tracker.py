"""
Track commits for auto-update detection and incremental processing
"""
from google.cloud import storage
from typing import Optional, Dict, Tuple, List
import json
from datetime import datetime
from .storage_utils import get_shared_repo_path


class CommitTracker:
    """
    Track last processed commits to enable:
    - Incremental updates (only process if new commits)
    - Commit history
    - Auto-update detection
    """
    
    def __init__(self, project_id: str, bucket_name: str):
        self.client = storage.Client(project=project_id)
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(bucket_name)
    
    def get_last_commit(self, repo_full_name: str) -> Optional[Dict]:
        """
        Get last processed commit info
        
        Args:
            repo_full_name: owner/repo
            
        Returns:
            Dict with commit_sha, branch, author, processed_at
        """
        repo_path = get_shared_repo_path(repo_full_name)
        blob = self.bucket.blob(f"{repo_path}/commit_info.json")
        
        if blob.exists():
            try:
                return json.loads(blob.download_as_text())
            except Exception as e:
                print(f"⚠️  Could not load commit info: {e}")
                return None
        return None
    
    def save_commit_info(self, repo_full_name: str, commit_sha: str, 
                        branch: str, author: str, commit_message: Optional[str] = None):
        """
        Save commit information after processing
        
        Args:
            repo_full_name: owner/repo
            commit_sha: Git commit SHA
            branch: Branch name
            author: Commit author
            commit_message: Commit message (optional)
        """
        repo_path = get_shared_repo_path(repo_full_name)
        
        commit_info = {
            'commit_sha': commit_sha,
            'branch': branch,
            'author': author,
            'commit_message': commit_message,
            'processed_at': datetime.now().isoformat(),
            'processor_version': '1.0.0'
        }
        
        # Also save commit history
        self._append_commit_history(repo_path, commit_info)
        
        blob = self.bucket.blob(f"{repo_path}/commit_info.json")
        blob.upload_from_string(json.dumps(commit_info, indent=2))
        print(f"✓ Saved commit info: {commit_sha[:8]} on {branch} by {author}")
    
    def needs_update(self, repo_full_name: str, current_sha: str) -> Tuple[bool, str]:
        """
        Check if repo needs re-processing
        
        Args:
            repo_full_name: owner/repo
            current_sha: Current commit SHA
            
        Returns:
            (needs_update: bool, reason: str)
        """
        last_commit = self.get_last_commit(repo_full_name)
        
        if not last_commit:
            return True, "First time indexing - no previous commit found"
        
        last_sha = last_commit.get('commit_sha')
        
        if last_sha == current_sha:
            return False, f"Already up to date (SHA: {current_sha[:8]})"
        
        return True, f"New commits detected: {last_sha[:8]} → {current_sha[:8]}"
    
    def _append_commit_history(self, repo_path: str, commit_info: Dict):
        """Append to commit history log"""
        blob = self.bucket.blob(f"{repo_path}/commit_history.jsonl")
        
        # Append to history
        history_line = json.dumps(commit_info) + '\n'
        
        if blob.exists():
            existing = blob.download_as_text()
            blob.upload_from_string(existing + history_line)
        else:
            blob.upload_from_string(history_line)
    
    def get_commit_history(self, repo_full_name: str, limit: int = 10) -> List[Dict]:
        """
        Get commit processing history
        
        Args:
            repo_full_name: owner/repo
            limit: Max number of entries to return
            
        Returns:
            List of commit info dicts (newest first)
        """
        repo_path = get_shared_repo_path(repo_full_name)
        blob = self.bucket.blob(f"{repo_path}/commit_history.jsonl")
        
        if not blob.exists():
            return []
        
        try:
            content = blob.download_as_text()
            lines = content.strip().split('\n')
            
            # Parse and reverse (newest first)
            history = [json.loads(line) for line in lines if line.strip()]
            history.reverse()
            
            return history[:limit]
        except Exception as e:
            print(f"⚠️  Could not load commit history: {e}")
            return []