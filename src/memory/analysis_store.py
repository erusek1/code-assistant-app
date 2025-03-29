#!/usr/bin/env python3
"""
Analysis Store - Stores and retrieves analysis results
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class AnalysisStore:
    """
    Stores and retrieves analysis results.
    """
    
    def __init__(self, store_path: Path):
        """
        Initialize the analysis store.
        
        Args:
            store_path: Path to the analysis store file
        """
        self.store_path = store_path
        self.analyses = self._load_store()
    
    def _load_store(self) -> Dict[str, Any]:
        """
        Load the analysis store from disk.
        
        Returns:
            Dictionary containing analysis results
        """
        if not self.store_path.exists():
            return {"analyses": []}
        
        try:
            with open(self.store_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"analyses": []}
        except Exception as e:
            print(f"Error loading analysis store: {e}")
            return {"analyses": []}
    
    def _save_store(self):
        """
        Save the analysis store to disk.
        """
        # Ensure parent directory exists
        self.store_path.parent.mkdir(exist_ok=True, parents=True)
        
        try:
            with open(self.store_path, "w") as f:
                json.dump(self.analyses, f, indent=2)
        except Exception as e:
            print(f"Error saving analysis store: {e}")
    
    def store_analysis(
        self,
        project_name: str,
        results: Dict[str, Any],
        overwrite: bool = True
    ) -> str:
        """
        Store an analysis result.
        
        Args:
            project_name: Name of the project
            results: Analysis results
            overwrite: Whether to overwrite existing results for the same project
            
        Returns:
            ID of the stored analysis
        """
        # Generate an ID for the analysis
        analysis_id = f"{project_name}_{int(time.time())}"
        
        # Create analysis entry
        analysis_entry = {
            "id": analysis_id,
            "project": project_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "issue_count": results.get("total_issues", 0),
            "file_count": results.get("files_analyzed", 0),
            "results": results
        }
        
        # If overwriting, remove existing analyses for the same project
        if overwrite:
            self.analyses["analyses"] = [a for a in self.analyses["analyses"] if a["project"] != project_name]
        
        # Add the new analysis
        self.analyses["analyses"].append(analysis_entry)
        
        # Save to disk
        self._save_store()
        
        return analysis_id
    
    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an analysis by ID.
        
        Args:
            analysis_id: ID of the analysis
            
        Returns:
            Analysis results, or None if not found
        """
        for analysis in self.analyses["analyses"]:
            if analysis["id"] == analysis_id:
                return analysis["results"]
        
        return None
    
    def get_latest_analysis(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest analysis for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Latest analysis results, or None if not found
        """
        # Get analyses for the project, sorted by timestamp (descending)
        project_analyses = [a for a in self.analyses["analyses"] if a["project"] == project_name]
        if not project_analyses:
            return None
        
        # Sort by timestamp (descending)
        project_analyses.sort(key=lambda a: a["timestamp"], reverse=True)
        
        # Return the latest
        return project_analyses[0]["results"]
    
    def list_analyses(self) -> List[Dict[str, Any]]:
        """
        List all analyses in the store.
        
        Returns:
            List of analysis entries
        """
        return [{
            "id": a["id"],
            "project": a["project"],
            "timestamp": a["timestamp"],
            "issue_count": a["issue_count"],
            "file_count": a["file_count"]
        } for a in self.analyses["analyses"]]
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete an analysis by ID.
        
        Args:
            analysis_id: ID of the analysis
            
        Returns:
            True if deleted, False if not found
        """
        initial_count = len(self.analyses["analyses"])
        self.analyses["analyses"] = [a for a in self.analyses["analyses"] if a["id"] != analysis_id]
        
        # Check if any were removed
        if len(self.analyses["analyses"]) < initial_count:
            self._save_store()
            return True
        
        return False