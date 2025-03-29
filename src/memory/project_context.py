#!/usr/bin/env python3
"""
Project Context - Manages context for a project
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class ProjectContext:
    """
    Manages context for a project, including file analyses and project metadata.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize the project context.
        
        Args:
            project_path: Path to the project
        """
        self.project_path = project_path
        self.project_name = project_path.name
        self.file_analyses = {}
        self.metadata = {
            "project_name": self.project_name,
            "project_path": str(project_path),
            "last_analysis": None,
        }
    
    @classmethod
    def load_or_create(cls, project_path: Path, context_path: Path) -> 'ProjectContext':
        """
        Load a project context from disk or create a new one.
        
        Args:
            project_path: Path to the project
            context_path: Path to the context file
            
        Returns:
            ProjectContext instance
        """
        if context_path.exists():
            try:
                with open(context_path, "r") as f:
                    data = json.load(f)
                
                # Create context instance
                context = cls(project_path)
                
                # Load data
                context.file_analyses = data.get("file_analyses", {})
                context.metadata = data.get("metadata", {
                    "project_name": context.project_name,
                    "project_path": str(project_path),
                    "last_analysis": None,
                })
                
                # Update project path if changed
                context.metadata["project_path"] = str(project_path)
                
                return context
                
            except Exception as e:
                print(f"Error loading project context: {e}")
                return cls(project_path)
        else:
            return cls(project_path)
    
    def save(self, context_path: Path):
        """
        Save the project context to disk.
        
        Args:
            context_path: Path to save the context to
        """
        # Ensure parent directory exists
        context_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Prepare data
        data = {
            "file_analyses": self.file_analyses,
            "metadata": self.metadata,
        }
        
        # Save to disk
        try:
            with open(context_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving project context: {e}")
    
    def update_file_analysis(self, file_path: str, analysis: Dict[str, Any]):
        """
        Update the analysis for a file.
        
        Args:
            file_path: Path to the file
            analysis: Analysis results for the file
        """
        self.file_analyses[file_path] = analysis
        self.metadata["last_analysis"] = analysis.get("analysis_timestamp")
    
    def get_file_analysis(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get the analysis for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Analysis results for the file, or None if not found
        """
        return self.file_analyses.get(file_path)
    
    def get_project_metadata(self) -> Dict[str, Any]:
        """
        Get the project metadata.
        
        Returns:
            Project metadata
        """
        return self.metadata
    
    def update_project_metadata(self, metadata: Dict[str, Any]):
        """
        Update the project metadata.
        
        Args:
            metadata: New metadata to merge with existing metadata
        """
        self.metadata.update(metadata)
    
    def clear_file_analyses(self):
        """
        Clear all file analyses.
        """
        self.file_analyses = {}
    
    def remove_file_analysis(self, file_path: str) -> bool:
        """
        Remove the analysis for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if removed, False if not found
        """
        if file_path in self.file_analyses:
            del self.file_analyses[file_path]
            return True
        return False