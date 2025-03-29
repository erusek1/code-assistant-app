#!/usr/bin/env python3
"""
File Service - Handles file system operations
"""
import os
import json
import fnmatch
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set

import config

class FileService:
    """
    Handles file system operations for the Code Assistant.
    """
    
    def get_code_files(self, directory: Path) -> List[Path]:
        """
        Get all code files in a directory recursively.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of file paths
        """
        files = []
        
        for root, _, filenames in os.walk(directory):
            # Skip excluded directories
            if any(fnmatch.fnmatch(root, pattern) for pattern in config.EXCLUDE_PATTERNS):
                continue
                
            # Check each file
            for filename in filenames:
                file_path = Path(os.path.join(root, filename))
                
                # Skip excluded files
                if any(fnmatch.fnmatch(str(file_path), pattern) for pattern in config.EXCLUDE_PATTERNS):
                    continue
                
                # Check if file extension is supported
                if file_path.suffix.lower() in config.CODE_EXTENSIONS:
                    files.append(file_path)
        
        return files
    
    def get_file_content(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the content and language of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (content, language)
        """
        # Check if file exists
        if not file_path.exists():
            print(f"Warning: File '{file_path}' does not exist")
            return None, None
        
        # Get language from extension
        extension = file_path.suffix.lower()
        if extension not in config.CODE_EXTENSIONS:
            print(f"Warning: File extension '{extension}' is not supported")
            return None, None
            
        language = config.CODE_EXTENSIONS[extension]
        
        # Special handling based on file type
        try:
            # JSON files - validate structure
            if extension == '.json':
                try:
                    # Try to parse JSON to validate it, then read raw content
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        json.load(f)
                    
                    # If successful, read file as text
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    
                    return content, language
                except json.JSONDecodeError as e:
                    print(f"Note: JSON parsing error in '{file_path}': {e}")
                    # Still return the content so we can analyze the invalid JSON
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    return content, language
            
            # Regular files - just read as text
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                return content, language
        except Exception as e:
            # Handle any other errors
            print(f"Error reading file '{file_path}': {e}")
            
            # Try binary mode as fallback for troublesome files
            try:
                with open(file_path, "rb") as f:
                    binary_content = f.read()
                    # Convert binary to string with explicit error handling
                    content = binary_content.decode("utf-8", errors="replace")
                    return content, language
            except Exception as e2:
                print(f"Binary fallback also failed for '{file_path}': {e2}")
                return None, None
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file information
        """
        try:
            # Get file stats
            stats = file_path.stat()
            
            # Create info dictionary
            info = {
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix,
                "size": stats.st_size,
                "modified": stats.st_mtime,
                "created": stats.st_ctime,
                "is_dir": file_path.is_dir(),
            }
            
            return info
        except Exception as e:
            print(f"Error getting file info for '{file_path}': {e}")
            return {
                "path": str(file_path),
                "name": file_path.name,
                "error": str(e)
            }
    
    def get_project_structure(self, directory: Path) -> Dict[str, Any]:
        """
        Get the structure of a project directory.
        
        Args:
            directory: Path to the project directory
            
        Returns:
            Dictionary representing the directory structure
        """
        result = {
            "name": directory.name,
            "path": str(directory),
            "type": "directory",
            "children": []
        }
        
        # Get excluded patterns
        exclude_patterns = config.EXCLUDE_PATTERNS
        
        try:
            for item in directory.iterdir():
                # Skip excluded items
                if any(fnmatch.fnmatch(str(item), pattern) for pattern in exclude_patterns):
                    continue
                
                # Get item info
                if item.is_dir():
                    # Recursively get structure for subdirectories
                    child = self.get_project_structure(item)
                    # Only add if it has children (not empty)
                    if child.get("children"):
                        result["children"].append(child)
                else:
                    # Add file
                    if item.suffix.lower() in config.CODE_EXTENSIONS:
                        result["children"].append({
                            "name": item.name,
                            "path": str(item),
                            "type": "file",
                            "extension": item.suffix,
                            "language": config.CODE_EXTENSIONS.get(item.suffix.lower(), "unknown")
                        })
        except Exception as e:
            print(f"Error getting project structure: {e}")
        
        return result
    
    def is_file_modified(self, file_path: Path, existing_analysis: Optional[Dict[str, Any]]) -> bool:
        """
        Check if a file has been modified since the last analysis.
        
        Args:
            file_path: Path to the file
            existing_analysis: Existing analysis for the file
            
        Returns:
            True if the file has been modified, False otherwise
        """
        if not existing_analysis:
            return True
        
        # Get file info
        file_info = self.get_file_info(file_path)
        
        # Get existing file info
        existing_file_info = existing_analysis.get("file_info", {})
        
        # Check if modified time has changed
        return file_info.get("modified") != existing_file_info.get("modified")