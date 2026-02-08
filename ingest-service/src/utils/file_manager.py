"""
File manager for saving documentation locally
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class DocumentationManager:
    """Manage documentation files locally"""
    
    def __init__(self, output_dir: str = "./docs"):
        """
        Initialize documentation manager
        
        Args:
            output_dir: Directory to save documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Documentation directory: {self.output_dir.absolute()}")
    
    def save_documentation(self, content: str, name: str, doc_type: str,
                          repo_name: Optional[str] = None) -> str:
        """
        Save documentation to a file
        
        Args:
            content: Documentation content
            name: Document name
            doc_type: Type (api, user_guide, technical, readme)
            repo_name: Optional repository name
            
        Returns:
            Path to saved file
        """
        # Create subdirectory for doc type
        doc_dir = self.output_dir / doc_type
        doc_dir.mkdir(exist_ok=True)
        
        # Sanitize filename
        safe_name = name.lower().replace(" ", "-")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in ["-", "_"])
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Create filename
        if repo_name:
            safe_repo = repo_name.replace("/", "-")
            filename = f"{safe_repo}_{safe_name}_{timestamp}.md"
        else:
            filename = f"{safe_name}_{timestamp}.md"
        
        filepath = doc_dir / filename
        
        # Write content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Documentation saved: {filepath}")
        
        return str(filepath)
    
    def save_edited_code(self, content: str, original_file: str,
                        repo_name: str, instruction: str) -> str:
        """
        Save edited code locally
        
        Args:
            content: Edited code content
            original_file: Original file path
            repo_name: Repository name
            instruction: Edit instruction
            
        Returns:
            Path to saved file
        """
        # Create edits directory
        edits_dir = self.output_dir / "code_edits"
        edits_dir.mkdir(exist_ok=True)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_repo = repo_name.replace("/", "-")
        safe_file = original_file.replace("/", "-")
        filename = f"{safe_repo}_{safe_file}_{timestamp}.py"
        
        filepath = edits_dir / filename
        
        # Write content with metadata
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Edited by Otto AI\n")
            f.write(f"# Original file: {original_file}\n")
            f.write(f"# Repository: {repo_name}\n")
            f.write(f"# Instruction: {instruction}\n")
            f.write(f"# Timestamp: {timestamp}\n")
            f.write(f"# {'='*60}\n\n")
            f.write(content)
        
        print(f"✓ Edited code saved: {filepath}")
        
        return str(filepath)