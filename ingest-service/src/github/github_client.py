# ingest-service/src/github/github_client.py
"""
GitHub Client for pushing code changes and documentation
"""
import os
from typing import Dict, Optional
from github import Github, GithubException
from datetime import datetime
import time


class GitHubClient:
    """
    GitHub client for:
    - Creating branches
    - Committing code changes
    - Creating pull requests
    - Pushing documentation
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub client
        
        Args:
            github_token: GitHub personal access token or OAuth token
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
        if not self.github_token:
            raise ValueError("GitHub token required")
        
        self.github = Github(self.github_token)
        print("✓ GitHub client initialized")
    
    def create_branch_and_push_code(self, repo_path: str, file_path: str,
                                    new_content: str, instruction: str,
                                    branch_name: Optional[str] = None) -> Dict:
        """
        Create a new branch, push code changes, and create a PR
        
        Args:
            repo_path: Repository path (e.g., 'repos/otto-pm/otto' or 'otto-pm/otto')
            file_path: File to modify (e.g., 'backend/app/routes/webhook.py')
            new_content: New file content
            instruction: Description of changes
            branch_name: Optional custom branch name
            
        Returns:
            Dictionary with branch info and PR link
        """
        try:
            # Clean repo path (remove 'repos/' prefix if present)
            if repo_path.startswith('repos/'):
                repo_path = repo_path.replace('repos/', '')
            
            # Get repository
            print(f"📦 Accessing repository: {repo_path}")
            repo = self.github.get_repo(repo_path)
            print(f"✓ Repository found: {repo.full_name}")
            
            # Check permissions
            if not repo.permissions.push:
                return {
                    'success': False,
                    'error': 'No push permissions for this repository'
                }
            
            # Generate branch name if not provided
            if not branch_name:
                timestamp = int(time.time())
                # Sanitize instruction for branch name
                safe_instruction = instruction.lower()[:30].replace(" ", "-")
                safe_instruction = "".join(c for c in safe_instruction if c.isalnum() or c == "-")
                branch_name = f"otto-edit-{safe_instruction}-{timestamp}"
            
            print(f"📌 Branch name: {branch_name}")
            
            # Get default branch
            default_branch = repo.default_branch
            source_branch = repo.get_branch(default_branch)
            print(f"✓ Base branch: {default_branch} (SHA: {source_branch.commit.sha[:8]})")
            
            # Create new branch
            try:
                repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=source_branch.commit.sha
                )
                print(f"✓ Created branch: {branch_name}")
            except GithubException as e:
                if e.status == 422:  # Branch already exists
                    print(f"⚠️  Branch {branch_name} already exists, using it")
                else:
                    raise
            
            # Get or create the file
            commit_message = f"Otto AI Edit: {instruction}\n\nAutomated code modification by Otto AI assistant."
            
            try:
                # File exists - update it
                file_contents = repo.get_contents(file_path, ref=default_branch)
                print(f"✓ Found existing file: {file_path}")
                
                result = repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    sha=file_contents.sha,
                    branch=branch_name
                )
                
                print(f"✓ Updated file on branch {branch_name}")
                
            except GithubException as e:
                if e.status == 404:
                    # File doesn't exist - create it
                    print(f"📝 Creating new file: {file_path}")
                    
                    result = repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=new_content,
                        branch=branch_name
                    )
                    
                    print(f"✓ Created new file on branch {branch_name}")
                else:
                    raise
            
            # Create pull request
            pr_title = f"🤖 Otto AI: {instruction[:50]}"
            pr_body = f"""## 🤖 Automated Code Edit by Otto AI

**Instruction:** {instruction}

**Modified File:** `{file_path}`

**Branch:** `{branch_name}`

---

### 📝 Changes Summary

{self._extract_change_summary(new_content)}

### ✅ Review Instructions

1. Review the changes in `{file_path}`
2. Run tests to ensure functionality
3. Merge if changes are satisfactory

---

*This pull request was automatically generated by [Otto AI](https://github.com/otto-pm/otto)*
"""
            
            try:
                pr = repo.create_pull(
                    title=pr_title,
                    body=pr_body,
                    head=branch_name,
                    base=default_branch
                )
                
                print(f"✓ Pull request created: #{pr.number}")
                print(f"  URL: {pr.html_url}")
                
                return {
                    'success': True,
                    'branch': branch_name,
                    'commit_sha': result['commit'].sha,
                    'pr_url': pr.html_url,
                    'pr_number': pr.number,
                    'file_path': file_path,
                    'base_branch': default_branch
                }
                
            except GithubException as e:
                if e.status == 422:  # PR already exists or no changes
                    # Try to find existing PR
                    existing_prs = repo.get_pulls(state='open', head=f"{repo.owner.login}:{branch_name}")
                    pr_list = list(existing_prs)
                    
                    if pr_list:
                        existing_pr = pr_list[0]
                        print(f"⚠️  PR already exists: {existing_pr.html_url}")
                        return {
                            'success': True,
                            'branch': branch_name,
                            'commit_sha': result['commit'].sha,
                            'pr_url': existing_pr.html_url,
                            'pr_number': existing_pr.number,
                            'message': 'Changes committed, PR already exists'
                        }
                    else:
                        print(f"⚠️  Changes committed but couldn't create PR: {e}")
                        return {
                            'success': True,
                            'branch': branch_name,
                            'commit_sha': result['commit'].sha,
                            'pr_url': None,
                            'message': f'Changes committed to branch {branch_name}, but PR creation failed'
                        }
                else:
                    raise
                
        except GithubException as e:
            error_msg = f"GitHub API error: {e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def push_documentation(self, repo_path: str, doc_content: str,
                          doc_name: str, doc_type: str = 'api',
                          create_pr: bool = True) -> Dict:
        """
        Push documentation to repository
        
        Args:
            repo_path: Repository path (owner/repo)
            doc_content: Documentation content (Markdown)
            doc_name: Name for the documentation file
            doc_type: Type of documentation (api, user_guide, technical, readme)
            create_pr: Whether to create a PR
            
        Returns:
            Dictionary with commit/PR info
        """
        try:
            # Clean repo path
            if repo_path.startswith('repos/'):
                repo_path = repo_path.replace('repos/', '')
            
            repo = self.github.get_repo(repo_path)
            
            # Determine file path
            if doc_type == 'readme':
                file_path = 'README.md'
            else:
                # Sanitize doc name
                safe_name = doc_name.lower().replace(" ", "-")
                safe_name = "".join(c for c in safe_name if c.isalnum() or c in ["-", "_"])
                file_path = f"docs/{doc_type}/{safe_name}.md"
            
            print(f"📄 Documentation path: {file_path}")
            
            # Create branch and commit
            return self.create_branch_and_push_code(
                repo_path=repo_path,
                file_path=file_path,
                new_content=doc_content,
                instruction=f"Add {doc_type} documentation for {doc_name}"
            )
                
        except Exception as e:
            print(f"❌ Error pushing documentation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_change_summary(self, content: str, max_lines: int = 10) -> str:
        """Extract a summary of changes from content"""
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return f"```\n{content}\n```"
        else:
            preview = '\n'.join(lines[:max_lines])
            return f"```\n{preview}\n...\n({len(lines) - max_lines} more lines)\n```"