"""
Storage utilities for multi-tenant architecture
Implements shared chunk storage with per-user metadata
"""
from typing import Optional, Dict, List
from google.cloud import storage
import json
from datetime import datetime


def get_shared_repo_path(repo_full_name: str) -> str:
    """
    Get shared repository path (single source of truth for chunks)
    
    Args:
        repo_full_name: owner/repo
        
    Returns:
        repos/{owner}/{repo}
        
    Example:
        get_shared_repo_path("otto-pm/otto") → "repos/otto-pm/otto"
    """
    return f"repos/{repo_full_name}"


def get_user_metadata_path(user_id: str, repo_full_name: str) -> str:
    """
    Get user-specific metadata path
    
    Args:
        user_id: User's GitHub ID
        repo_full_name: owner/repo
        
    Returns:
        user_data/{user_id}/repos/{owner}/{repo}
        
    Example:
        get_user_metadata_path("123", "otto-pm/otto") → "user_data/123/repos/otto-pm/otto"
    """
    return f"user_data/{user_id}/repos/{repo_full_name}"


def parse_repo_path(path: str) -> dict:
    """
    Parse a storage path to extract components
    
    Args:
        path: Storage path
        
    Returns:
        Dict with: user_id, owner, repo, repo_full_name, is_user_specific
    """
    parts = path.split('/')
    
    if parts[0] == 'repos':
        # Shared: repos/{owner}/{repo}
        return {
            'user_id': None,
            'owner': parts[1],
            'repo': parts[2],
            'repo_full_name': f"{parts[1]}/{parts[2]}",
            'is_user_specific': False,
            'storage_type': 'shared'
        }
    elif parts[0] == 'user_data':
        # User-specific: user_data/{user_id}/repos/{owner}/{repo}
        return {
            'user_id': parts[1],
            'owner': parts[3],
            'repo': parts[4],
            'repo_full_name': f"{parts[3]}/{parts[4]}",
            'is_user_specific': True,
            'storage_type': 'user_metadata'
        }
    else:
        # Legacy format: {owner}/{repo}
        return {
            'user_id': None,
            'owner': parts[0],
            'repo': parts[1],
            'repo_full_name': f"{parts[0]}/{parts[1]}",
            'is_user_specific': False,
            'storage_type': 'legacy'
        }


class UserRepoAccess:
    """
    Manage user access tracking and permissions
    
    Stores which users have accessed which repos and their permissions
    """
    
    def __init__(self, project_id: str, bucket_name: str):
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)
    
    def record_user_access(self, user_id: str, repo_full_name: str, 
                          access_level: str = 'read', 
                          github_permissions: Optional[Dict] = None):
        """
        Record that a user accessed a repository
        
        Args:
            user_id: User's GitHub ID
            repo_full_name: owner/repo
            access_level: read, write, admin
            github_permissions: User's actual GitHub permissions
        """
        metadata_path = get_user_metadata_path(user_id, repo_full_name)
        blob = self.bucket.blob(f"{metadata_path}/access_info.json")
        
        access_info = {
            'user_id': user_id,
            'repo': repo_full_name,
            'access_level': access_level,
            'github_permissions': github_permissions or {},
            'first_accessed': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'access_count': 1
        }
        
        # Update if already exists
        if blob.exists():
            try:
                existing = json.loads(blob.download_as_text())
                access_info['first_accessed'] = existing.get('first_accessed', access_info['first_accessed'])
                access_info['access_count'] = existing.get('access_count', 0) + 1
            except Exception as e:
                print(f"⚠️  Could not load existing access info: {e}")
        
        blob.upload_from_string(json.dumps(access_info, indent=2))
        print(f"✓ Recorded access: user {user_id} → {repo_full_name} (count: {access_info['access_count']})")
    
    def get_access_info(self, user_id: str, repo_full_name: str) -> Optional[Dict]:
        """
        Get user's access info for a specific repo
        
        Args:
            user_id: User's GitHub ID
            repo_full_name: owner/repo
            
        Returns:
            Access info dict or None if not found
        """
        metadata_path = get_user_metadata_path(user_id, repo_full_name)
        blob = self.bucket.blob(f"{metadata_path}/access_info.json")
        
        if blob.exists():
            return json.loads(blob.download_as_text())
        return None
    
    def get_user_repos(self, user_id: str) -> List[str]:
        """Get all repositories a user has accessed"""
        prefix = f"user_data/{user_id}/repos/"
        
        print(f"🔍 Looking for user repos: {prefix}")
        
        # List all blobs with this prefix
        all_blobs = list(self.bucket.list_blobs(prefix=prefix))
        
        print(f"   Found {len(all_blobs)} blobs")
        
        repos = set()
        
        for blob in all_blobs:
            # user_data/{user_id}/repos/{owner}/{repo}/access_info.json
            parts = blob.name.split('/')
            print(f"   Blob: {blob.name}")
            
            if len(parts) >= 6 and parts[5] == 'access_info.json':
                owner, repo_name = parts[3], parts[4]
                repos.add(f"{owner}/{repo_name}")
        
        print(f"   Repos found: {repos}")
        
        return sorted(list(repos))
    
    def has_user_accessed_repo(self, user_id: str, repo_full_name: str) -> bool:
        """
        Check if user has previously accessed this repo
        
        Args:
            user_id: User's GitHub ID
            repo_full_name: owner/repo
            
        Returns:
            True if user has accessed this repo before
        """
        metadata_path = get_user_metadata_path(user_id, repo_full_name)
        blob = self.bucket.blob(f"{metadata_path}/access_info.json")
        return blob.exists()
    
    def save_user_preferences(self, user_id: str, repo_full_name: str, 
                            preferences: Dict):
        """
        Save user's preferences for a repository
        
        Args:
            user_id: User's GitHub ID
            repo_full_name: owner/repo
            preferences: User preferences dict
        """
        metadata_path = get_user_metadata_path(user_id, repo_full_name)
        blob = self.bucket.blob(f"{metadata_path}/preferences.json")
        
        pref_data = {
            'preferred_doc_type': preferences.get('doc_type', 'api'),
            'preferred_chunk_size': preferences.get('chunk_size', 150),
            'auto_push_prs': preferences.get('auto_push', False),
            'favorite': preferences.get('favorite', False),
            'notifications': preferences.get('notifications', True),
            'updated_at': datetime.now().isoformat()
        }
        
        blob.upload_from_string(json.dumps(pref_data, indent=2))
        print(f"✓ Saved preferences for user {user_id} on {repo_full_name}")
    
    def get_user_preferences(self, user_id: str, repo_full_name: str) -> Dict:
        """Get user's preferences for a repository"""
        metadata_path = get_user_metadata_path(user_id, repo_full_name)
        blob = self.bucket.blob(f"{metadata_path}/preferences.json")
        
        if blob.exists():
            return json.loads(blob.download_as_text())
        
        # Default preferences
        return {
            'preferred_doc_type': 'api',
            'preferred_chunk_size': 150,
            'auto_push_prs': False,
            'favorite': False,
            'notifications': True
        }