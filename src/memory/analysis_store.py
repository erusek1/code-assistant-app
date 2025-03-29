"""
Analysis Store - Storage for analysis results
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class AnalysisStore:
    """
    Storage for analysis results.
    """
    
    def __init__(self, store_path: Path):
        """
        Initialize the analysis store.
        
        Args:
            store_path: Path to the analysis store file
        """
        self.store_path = store_path
        self._ensure_store_exists()
    
    def store_analysis(self, project_name: str, results: Dict[str, Any]) -> None:
        """
        Store analysis results.
        
        Args:
            project_name: Name of the project
            results: Analysis results
        """
        # Load existing store
        store = self._load_store()
        
        # Create project entry if it doesn't exist
        if project_name not in store:
            store[project_name] = []
        
        # Add analysis to project
        analysis_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "unix_timestamp": time.time(),
            "project": project_name,
            "issue_count": results.get("total_issues", 0),
            "files_analyzed": results.get("files_analyzed", 0),
            "results": results
        }
        
        store[project_name].append(analysis_entry)
        
        # Trim to keep only the last 10 analyses per project
        if len(store[project_name]) > 10:
            store[project_name] = sorted(
                store[project_name],
                key=lambda x: x["unix_timestamp"],
                reverse=True
            )[:10]
        
        # Save store
        self._save_store(store)
    
    def get_analysis(self, project_name: str, index: int = 0) -> Optional[Dict[str, Any]]:
        """
        Get analysis results.
        
        Args:
            project_name: Name of the project
            index: Index of the analysis (0 = most recent)
            
        Returns:
            Analysis results or None if not found
        """
        # Load existing store
        store = self._load_store()
        
        # Check if project exists
        if project_name not in store:
            return None
        
        # Get analyses for project
        analyses = store[project_name]
        
        # Sort by timestamp (most recent first)
        analyses = sorted(analyses, key=lambda x: x["unix_timestamp"], reverse=True)
        
        # Check if index is valid
        if index >= len(analyses):
            return None
        
        return analyses[index]
    
    def get_latest_analysis(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest analysis results for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Latest analysis results or None if not found
        """
        return self.get_analysis(project_name, 0)
    
    def list_analyses(self) -> List[Dict[str, Any]]:
        """
        List all analyses.
        
        Returns:
            List of analyses
        """
        # Load existing store
        store = self._load_store()
        
        # Collect all analyses
        analyses = []
        for project_name, project_analyses in store.items():
            for analysis in project_analyses:
                analyses.append({
                    "project": project_name,
                    "timestamp": analysis["timestamp"],
                    "unix_timestamp": analysis["unix_timestamp"],
                    "issue_count": analysis["issue_count"],
                    "files_analyzed": analysis["files_analyzed"]
                })
        
        # Sort by timestamp (most recent first)
        analyses = sorted(analyses, key=lambda x: x["unix_timestamp"], reverse=True)
        
        return analyses
    
    def _ensure_store_exists(self) -> None:
        """
        Ensure that the analysis store file exists.
        """
        # Create parent directories if they don't exist
        self.store_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Create store file if it doesn't exist
        if not self.store_path.exists():
            self._save_store({})
    
    def _load_store(self) -> Dict[str, Any]:
        """
        Load the analysis store.
        
        Returns:
            Analysis store data
        """
        try:
            with open(self.store_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_store(self, store: Dict[str, Any]) -> None:
        """
        Save the analysis store.
        
        Args:
            store: Analysis store data
        """
        with open(self.store_path, 'w') as f:
            json.dump(store, f, indent=2)