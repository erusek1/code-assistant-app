#!/usr/bin/env python3
"""
Code Fixer - Fixes issues found by the Code Analyzer
"""
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Optional

from src.llm.llm_service import LLMService
from src.utils.file_service import FileService
from src.memory.project_context import ProjectContext
import config

class CodeFixer:
    """
    Fixes issues in code based on analysis results.
    """
    
    def __init__(
        self,
        file_service: FileService,
        llm_service: LLMService,
        project_context: ProjectContext
    ):
        self.file_service = file_service
        self.llm_service = llm_service
        self.project_context = project_context
        
        # Statistics
        self.files_fixed = 0
        self.issues_fixed = 0
        self.total_tokens = 0
    
    def fix_from_analysis(self, analysis_report: str, project_path: Path) -> Dict[str, str]:
        """
        Fix issues based on an analysis report.
        
        Args:
            analysis_report: Content of the analysis report
            project_path: Path to the project directory
            
        Returns:
            Dictionary mapping file paths to fixed content
        """
        # Extract file paths and issues from the report
        file_issues = self._extract_file_issues(analysis_report)
        
        # Fix each file
        fixed_files = {}
        
        for file_path, issues in file_issues.items():
            abs_path = project_path / file_path
            if not abs_path.exists():
                print(f"Warning: File '{file_path}' does not exist, skipping")
                continue
                
            print(f"Fixing file: {file_path} ({len(issues)} issues)")
            
            # Get file content and language
            content, language = self.file_service.get_file_content(abs_path)
            
            if not content or not language:
                print(f"Warning: Could not read file '{file_path}', skipping")
                continue
                
            # Get project context for the file
            file_context = self.project_context.get_file_analysis(str(abs_path))
            
            # Fix issues
            fixed_content, tokens_used = self.llm_service.generate_fixes(
                code=content,
                language=language,
                file_path=str(file_path),
                issues=issues,
                context=file_context.get("standard_analysis") if file_context else None
            )
            
            # Update statistics
            self.files_fixed += 1
            self.issues_fixed += len(issues)
            self.total_tokens += tokens_used
            
            # Add to fixed files
            fixed_files[str(abs_path)] = fixed_content
        
        print(f"Fixed {self.issues_fixed} issues across {self.files_fixed} files.")
        return fixed_files
    
    def _extract_file_issues(self, analysis_report: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract file paths and issues from an analysis report.
        
        Args:
            analysis_report: Content of the analysis report
            
        Returns:
            Dictionary mapping file paths to lists of issues
        """
        file_issues = {}
        
        # Regular expression to find file sections in the report
        file_pattern = r"^## File: (.+)$"
        issue_pattern = r"^### Issue #\d+\s*(?:\(Lines?\s+([\d-]+)\))?:\s*(.+?)$"
        
        current_file = None
        current_issues = []
        
        for line in analysis_report.split("\n"):
            # Check if this is a file header
            file_match = re.match(file_pattern, line)
            if file_match:
                # If we were already processing a file, save its issues
                if current_file and current_issues:
                    file_issues[current_file] = current_issues
                    
                # Start a new file
                current_file = file_match.group(1)
                current_issues = []
                continue
                
            # If we're not processing a file yet, skip
            if not current_file:
                continue
                
            # Check if this is an issue
            issue_match = re.match(issue_pattern, line)
            if issue_match:
                line_number = issue_match.group(1)
                description = issue_match.group(2).strip()
                
                # Add to current issues
                current_issues.append({
                    "line_number": line_number,
                    "description": description,
                    "fixed": False
                })
        
        # Add the last file
        if current_file and current_issues:
            file_issues[current_file] = current_issues
            
        return file_issues
    
    def apply_fixes(self, fixed_files: Dict[str, str], dry_run: bool = False) -> List[str]:
        """
        Apply fixes to actual files.
        
        Args:
            fixed_files: Dictionary mapping file paths to fixed content
            dry_run: If True, don't actually modify files
            
        Returns:
            List of paths to files that were modified
        """
        modified_files = []
        
        for file_path, fixed_content in fixed_files.items():
            path = Path(file_path)
            
            # Compare with original content
            original_content, _ = self.file_service.get_file_content(path)
            if original_content == fixed_content:
                print(f"No changes needed for {path}")
                continue
                
            if dry_run:
                print(f"Would modify: {path}")
            else:
                # Create backup
                backup_path = path.with_suffix(path.suffix + ".bak")
                with open(backup_path, "w") as f:
                    f.write(original_content)
                    
                # Write fixed content
                with open(path, "w") as f:
                    f.write(fixed_content)
                    
                print(f"Modified: {path} (backup at {backup_path})")
            
            modified_files.append(str(path))
        
        return modified_files