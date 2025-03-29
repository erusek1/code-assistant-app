"""
Project Context - Context for project-wide understanding
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class ProjectContext:
    """
    Context for project-wide understanding.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize the project context.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = project_path
        self.project_name = project_path.name
        
        # Dictionaries to store context
        self.file_analyses = {}  # Stores analysis results for each file
        self.file_contexts = {}  # Stores additional context for each file
        self.project_context = {}  # Stores project-level context
    
    @classmethod
    def load_or_create(cls, project_path: Path, context_path: Path) -> 'ProjectContext':
        """
        Load project context from file or create a new one.
        
        Args:
            project_path: Path to the project directory
            context_path: Path to the context file
            
        Returns:
            ProjectContext instance
        """
        # Create new context
        context = cls(project_path)
        
        # Try to load existing context
        try:
            if context_path.exists():
                with open(context_path, 'r') as f:
                    data = json.load(f)
                
                # Only load if it's for the same project
                if data.get("project_name") == project_path.name:
                    context.file_analyses = data.get("file_analyses", {})
                    context.file_contexts = data.get("file_contexts", {})
                    context.project_context = data.get("project_context", {})
        except Exception as e:
            print(f"Error loading project context: {e}")
        
        return context
    
    def save(self, context_path: Path) -> None:
        """
        Save project context to file.
        
        Args:
            context_path: Path to the context file
        """
        # Create data dictionary
        data = {
            "project_name": self.project_name,
            "file_analyses": self.file_analyses,
            "file_contexts": self.file_contexts,
            "project_context": self.project_context
        }
        
        # Create parent directories if they don't exist
        context_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Save to file
        with open(context_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_file_analysis(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Analysis results or None if not found
        """
        return self.file_analyses.get(file_path)
    
    def update_file_analysis(self, file_path: str, analysis: Dict[str, Any]) -> None:
        """
        Update analysis for a file.
        
        Args:
            file_path: Path to the file
            analysis: Analysis results
        """
        self.file_analyses[file_path] = analysis
    
    def get_file_context(self, file_path: str) -> Optional[str]:
        """
        Get context for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Context or None if not found
        """
        return self.file_contexts.get(file_path)
    
    def update_file_context(self, file_path: str, context: str) -> None:
        """
        Update context for a file.
        
        Args:
            file_path: Path to the file
            context: Context to store
        """
        self.file_contexts[file_path] = context
    
    def get_project_context(self, key: str) -> Any:
        """
        Get project-level context.
        
        Args:
            key: Context key
            
        Returns:
            Context value or None if not found
        """
        return self.project_context.get(key)
    
    def update_project_context(self, key: str, value: Any) -> None:
        """
        Update project-level context.
        
        Args:
            key: Context key
            value: Context value
        """
        self.project_context[key] = value
    
    def get_all_file_paths(self) -> List[str]:
        """
        Get all file paths with analysis.
        
        Returns:
            List of file paths
        """
        return list(self.file_analyses.keys())
    
    def get_related_files(self, file_path: str, max_files: int = 5) -> List[str]:
        """
        Get related files based on similar issues or context.
        
        Args:
            file_path: Path to the file
            max_files: Maximum number of files to return
            
        Returns:
            List of related file paths
        """
        file_analysis = self.get_file_analysis(file_path)
        if not file_analysis:
            return []
        
        # Get issues for the file
        issues = file_analysis.get("issues", [])
        if not issues:
            return []
        
        # Count related files by common issues
        related_counts = {}
        for other_path, other_analysis in self.file_analyses.items():
            # Skip the same file
            if other_path == file_path:
                continue
                
            # Get issues for the other file
            other_issues = other_analysis.get("issues", [])
            if not other_issues:
                continue
            
            # Count common issues
            common_count = 0
            for issue in issues:
                issue_desc = issue.get("description", "")
                if not issue_desc:
                    continue
                    
                # Find similar issues
                for other_issue in other_issues:
                    other_desc = other_issue.get("description", "")
                    if not other_desc:
                        continue
                        
                    # Check for similarity
                    # (simple approach: check if the shorter is a substring of the longer)
                    if len(issue_desc) < len(other_desc):
                        if issue_desc in other_desc:
                            common_count += 1
                    else:
                        if other_desc in issue_desc:
                            common_count += 1
            
            # Add to related counts if there are common issues
            if common_count > 0:
                related_counts[other_path] = common_count
        
        # Sort by common issue count (descending)
        related_files = sorted(
            related_counts.keys(),
            key=lambda path: related_counts[path],
            reverse=True
        )
        
        return related_files[:max_files]