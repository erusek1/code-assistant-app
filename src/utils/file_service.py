"""
File Service - Handles file system operations
"""
import os
import json
import fnmatch
import chardet
import traceback
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
        
        try:
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
        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")
            traceback.print_exc()
        
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
        
        # Try different approaches to read the file based on type
        try:
            # Special handling for JSON files
            if extension == '.json':
                try:
                    # First try to read and validate JSON
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        # Try to parse as JSON
                        try:
                            json_data = json.load(f)
                            # If successful, read the file again as text
                            with open(file_path, "r", encoding="utf-8", errors="replace") as f2:
                                return f2.read(), language
                        except json.JSONDecodeError as je:
                            print(f"Warning: JSON parsing error in '{file_path}': {je}")
                            # Return the raw content for analysis
                            with open(file_path, "r", encoding="utf-8", errors="replace") as f2:
                                return f2.read(), language
                except Exception as e:
                    print(f"Error reading JSON file '{file_path}': {e}")
                    # Fall through to binary approach
            
            # Try standard text reading first
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    return content, language
            except UnicodeDecodeError:
                # If UTF-8 fails, detect encoding and try again
                print(f"  Unicode error with {file_path}, attempting to detect encoding...")
                
                # Read file in binary mode to detect encoding
                with open(file_path, "rb") as f:
                    raw_data = f.read()
                    
                # Detect encoding
                result = chardet.detect(raw_data)
                encoding = result.get("encoding", "utf-8")
                confidence = result.get("confidence", 0)
                
                print(f"  Detected encoding: {encoding} with {confidence:.2f} confidence")
                
                # Try with detected encoding if confidence is high enough
                if confidence > 0.7:
                    with open(file_path, "r", encoding=encoding, errors="replace") as f:
                        content = f.read()
                        return content, language
                
                # Otherwise, force utf-8 with error replacement
                content = raw_data.decode("utf-8", errors="replace")
                return content, language
                
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")
            traceback.print_exc()
            
            # Last resort: try to read as binary and force to utf-8
            try:
                with open(file_path, "rb") as f:
                    raw_data = f.read()
                    content = raw_data.decode("utf-8", errors="replace")
                    return content, language
            except Exception as e2:
                print(f"Failed all reading attempts for '{file_path}': {e2}")
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