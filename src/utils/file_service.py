"""
File Service - File operations
"""
import os
import re
import fnmatch
import json
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import config

class FileService:
    """
    Service for file operations.
    """
    
    def get_code_files(self, directory_path: Path) -> List[Path]:
        """
        Get all code files in a directory recursively.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            List of code file paths
        """
        code_files = []
        
        # Walk through directory
        for root, _, files in os.walk(directory_path):
            # Check if the path should be excluded
            if self._should_exclude_path(root):
                continue
                
            # Process each file
            for file in files:
                file_path = Path(root) / file
                
                # Check if the file should be excluded
                if self._should_exclude_path(str(file_path)):
                    continue
                
                # Check if it's a code file
                _, ext = os.path.splitext(file)
                if ext.lower() in config.CODE_EXTENSIONS:
                    code_files.append(file_path)
        
        return code_files
    
    def get_file_content(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the content of a file and its language.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (content, language)
        """
        try:
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Check if it's a supported language
            if ext not in config.CODE_EXTENSIONS:
                return None, None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Get language
            language = config.CODE_EXTENSIONS[ext]
            
            return content, language
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
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
            stats = os.stat(file_path)
            
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Create file info dictionary
            file_info = {
                "path": str(file_path),
                "name": file_path.name,
                "size": stats.st_size,
                "line_count": self._count_lines(file_path),
                "extension": ext,
                "language": config.CODE_EXTENSIONS.get(ext),
                "last_modified": stats.st_mtime,
                "created": stats.st_ctime,
            }
            
            return file_info
        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return {
                "path": str(file_path),
                "error": str(e)
            }
    
    def get_project_structure(self, directory_path: Path) -> Dict[str, Any]:
        """
        Get the structure of a project.
        
        Args:
            directory_path: Path to the project directory
            
        Returns:
            Dictionary representing the project structure
        """
        structure = {
            "name": directory_path.name,
            "type": "directory",
            "children": []
        }
        
        # Build the structure recursively
        self._build_structure(directory_path, structure["children"])
        
        return structure
    
    def is_file_modified(self, file_path: Path, existing_analysis: Optional[Dict[str, Any]]) -> bool:
        """
        Check if a file has been modified since it was last analyzed.
        
        Args:
            file_path: Path to the file
            existing_analysis: Existing analysis of the file
            
        Returns:
            True if the file has been modified, False otherwise
        """
        if not existing_analysis:
            return True
        
        try:
            # Get file stats
            stats = os.stat(file_path)
            
            # Get last modified time
            last_modified = stats.st_mtime
            
            # Get last analyzed time
            last_analyzed = existing_analysis.get("file_info", {}).get("last_modified", 0)
            
            # Check if the file has been modified
            return last_modified > last_analyzed
        except Exception as e:
            print(f"Error checking if file {file_path} has been modified: {e}")
            return True
    
    def validate_code(self, code: str, language: str) -> bool:
        """
        Validate code for syntax errors.
        
        Args:
            code: Code to validate
            language: Programming language
            
        Returns:
            True if the code is valid, False otherwise
        """
        try:
            if language == "python":
                # Validate Python code
                ast.parse(code)
                return True
            elif language in ["javascript", "typescript"]:
                # Validate JavaScript/TypeScript code
                # Just check for basic syntax (brackets, parentheses, braces)
                if self._check_balanced_delimiters(code):
                    return True
            else:
                # No validation for other languages, assume it's valid
                return True
        except Exception as e:
            print(f"Error validating {language} code: {e}")
            return False
    
    def _should_exclude_path(self, path: str) -> bool:
        """
        Check if a path should be excluded.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        # Check against exclude patterns
        for pattern in config.EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(path, pattern):
                return True
        
        return False
    
    def _count_lines(self, file_path: Path) -> int:
        """
        Count the number of lines in a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return sum(1 for _ in f)
        except Exception as e:
            print(f"Error counting lines in {file_path}: {e}")
            return 0
    
    def _build_structure(self, path: Path, children: List[Dict[str, Any]]) -> None:
        """
        Build the structure of a directory recursively.
        
        Args:
            path: Path to the directory
            children: List to store children
        """
        # Skip excluded paths
        if self._should_exclude_path(str(path)):
            return
            
        try:
            # Process directory contents
            for item in sorted(path.iterdir()):
                # Skip excluded paths
                if self._should_exclude_path(str(item)):
                    continue
                    
                if item.is_dir():
                    # Directory
                    dir_info = {
                        "name": item.name,
                        "type": "directory",
                        "children": []
                    }
                    children.append(dir_info)
                    
                    # Recursively process subdirectory
                    self._build_structure(item, dir_info["children"])
                else:
                    # File
                    _, ext = os.path.splitext(item)
                    ext = ext.lower()
                    
                    # Only include code files
                    if ext in config.CODE_EXTENSIONS:
                        file_info = {
                            "name": item.name,
                            "type": "file",
                            "language": config.CODE_EXTENSIONS[ext],
                            "size": item.stat().st_size
                        }
                        children.append(file_info)
        except Exception as e:
            print(f"Error building structure for {path}: {e}")
    
    def _check_balanced_delimiters(self, code: str) -> bool:
        """
        Check if delimiters (parentheses, brackets, braces) are balanced.
        
        Args:
            code: Code to check
            
        Returns:
            True if delimiters are balanced, False otherwise
        """
        stack = []
        delimiters = {
            ')': '(',
            ']': '[',
            '}': '{',
        }
        
        for char in code:
            if char in '([{':
                stack.append(char)
            elif char in ')]}':
                if not stack or stack.pop() != delimiters[char]:
                    return False
        
        return len(stack) == 0