"""
Code Fixer - Implements fixes for issues identified in code analysis
"""
import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

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
        
        # Stats
        self.fixes_applied = 0
        self.files_fixed = 0
    
    def fix_from_analysis(self, analysis_report: str, project_path: Path) -> Dict[str, str]:
        """
        Fix issues based on analysis report.
        
        Args:
            analysis_report: Analysis report content
            project_path: Path to the project directory
            
        Returns:
            Dictionary mapping file paths to fixed content
        """
        # Reset stats
        self.fixes_applied = 0
        self.files_fixed = 0
        
        # Extract file analyses from report
        file_analyses = self._extract_file_analyses(analysis_report)
        
        # Dictionary to store fixed files
        fixed_files = {}
        
        # Fix each file
        for file_path_str, issues in file_analyses.items():
            file_path = Path(file_path_str)
            
            # Skip if file doesn't exist
            if not file_path.exists():
                print(f"Warning: File {file_path} does not exist, skipping.")
                continue
            
            # Get file content and language
            content, language = self.file_service.get_file_content(file_path)
            
            if not content or not language:
                continue
            
            # Fix issues in file
            print(f"Fixing issues in {file_path.relative_to(project_path)}")
            fixed_content = self._fix_file(file_path, content, language, issues)
            
            # If content was modified, add to fixed files
            if fixed_content != content:
                fixed_files[str(file_path)] = fixed_content
                self.files_fixed += 1
                
                # Update project context
                self._update_project_context(file_path, issues)
        
        print(f"Applied {self.fixes_applied} fixes to {self.files_fixed} files.")
        return fixed_files
    
    def fix_file(self, file_path: Path, issues: List[Dict[str, Any]]) -> Optional[str]:
        """
        Fix issues in a single file.
        
        Args:
            file_path: Path to the file
            issues: List of issues to fix
            
        Returns:
            Fixed content if modified, None otherwise
        """
        # Get file content and language
        content, language = self.file_service.get_file_content(file_path)
        
        if not content or not language:
            return None
        
        # Fix issues
        fixed_content = self._fix_file(file_path, content, language, issues)
        
        # Update project context
        if fixed_content != content:
            self._update_project_context(file_path, issues)
            
        return fixed_content if fixed_content != content else None
    
    def _extract_file_analyses(self, analysis_report: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract file analyses from analysis report.
        
        Args:
            analysis_report: Analysis report content
            
        Returns:
            Dictionary mapping file paths to lists of issues
        """
        file_analyses = {}
        
        # Check if the report is JSON
        try:
            # Try to parse as JSON
            data = json.loads(analysis_report)
            
            # Extract file analyses from JSON
            if "file_analyses" in data:
                for file_path, analysis in data["file_analyses"].items():
                    if "issues" in analysis:
                        file_analyses[file_path] = analysis["issues"]
            
            return file_analyses
        except json.JSONDecodeError:
            # Not JSON, parse as markdown/text
            pass
        
        # Parse markdown/text format
        # Look for file headings (# File: path/to/file.py)
        file_pattern = r"#\s*File:\s*(.+?)(?:\n|$)"
        file_matches = re.finditer(file_pattern, analysis_report)
        
        for file_match in file_matches:
            file_path = file_match.group(1).strip()
            
            # Find the section for this file
            start_pos = file_match.end()
            next_file_match = re.search(file_pattern, analysis_report[start_pos:])
            end_pos = start_pos + next_file_match.start() if next_file_match else len(analysis_report)
            file_section = analysis_report[start_pos:end_pos]
            
            # Extract issues
            issues = []
            
            # Look for issue sections
            issue_pattern = r"(?:Issue|Problem|Bug|Error|Warning)\s+\#?\d*\s*:\s*(.+?)(?:\n|$)"
            issue_matches = re.finditer(issue_pattern, file_section)
            
            for issue_match in issue_matches:
                desc = issue_match.group(1).strip()
                # Try to find line number
                line_match = re.search(r"(?:Line|Lines)\s+(\d+(?:-\d+)?)", file_section[issue_match.start():issue_match.end()])
                line_number = line_match.group(1) if line_match else None
                
                issues.append({
                    "line_number": line_number,
                    "description": desc,
                    "fixed": False,
                })
            
            # If no issues found with specific pattern, try bullet points
            if not issues:
                bullet_pattern = r"(?:^\s*-\s*|\n\s*-\s*)(.+?)(?:\n|$)"
                bullet_matches = re.finditer(bullet_pattern, file_section)
                
                for bullet_match in bullet_matches:
                    desc = bullet_match.group(1).strip()
                    if len(desc) > 10:  # Only add substantial descriptions
                        issues.append({
                            "line_number": None,
                            "description": desc,
                            "fixed": False,
                        })
            
            # Add to file analyses
            if issues:
                file_analyses[file_path] = issues
        
        return file_analyses
    
    def _fix_file(
        self,
        file_path: Path,
        content: str,
        language: str,
        issues: List[Dict[str, Any]]
    ) -> str:
        """
        Fix issues in a file.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            language: Programming language
            issues: List of issues to fix
            
        Returns:
            Fixed content
        """
        # If no issues, return original content
        if not issues:
            return content
        
        # Get context from project
        file_context = self.project_context.get_file_context(str(file_path))
        
        # Generate fixes with the LLM
        fixed_content, tokens_used = self.llm_service.generate_fixes(
            code=content,
            language=language,
            file_path=str(file_path),
            issues=issues,
            context=file_context
        )
        
        # Verify fixed content
        if not fixed_content or not fixed_content.strip():
            print(f"  Warning: Generated fix for {file_path.name} is empty, using original content.")
            return content
        
        # Check if fixed content is valid for the language
        is_valid = self.file_service.validate_code(fixed_content, language)
        if not is_valid:
            print(f"  Warning: Generated fix for {file_path.name} is not valid {language}, using original content.")
            return content
        
        # Update stats
        self.fixes_applied += len(issues)
        
        return fixed_content
    
    def _update_project_context(self, file_path: Path, issues: List[Dict[str, Any]]) -> None:
        """
        Update project context with fixed issues.
        
        Args:
            file_path: Path to the file
            issues: List of issues that were fixed
        """
        # Mark issues as fixed
        for issue in issues:
            issue["fixed"] = True
        
        # Get existing file analysis from context
        file_analysis = self.project_context.get_file_analysis(str(file_path))
        
        if file_analysis:
            # Update existing issues
            if "issues" in file_analysis:
                for i, existing_issue in enumerate(file_analysis["issues"]):
                    for fixed_issue in issues:
                        if existing_issue["description"] == fixed_issue["description"]:
                            file_analysis["issues"][i]["fixed"] = True
            
            # Update file analysis in context
            self.project_context.update_file_analysis(str(file_path), file_analysis)
        
        # Update file context
        self.project_context.update_file_context(
            file_path=str(file_path),
            context=f"Fixed issues: {', '.join(issue['description'][:50] + '...' if len(issue['description']) > 50 else issue['description'] for issue in issues)}"
        )