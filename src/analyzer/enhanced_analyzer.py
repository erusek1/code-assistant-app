#!/usr/bin/env python3
"""
Enhanced Code Analyzer - Analyzes code with improved issue detection and reporting
"""
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import json

from src.llm.llm_service import LLMService
from src.utils.file_service import FileService
from src.memory.project_context import ProjectContext
from src.memory.analysis_store import AnalysisStore
import config

class EnhancedAnalyzer:
    """
    An enhanced code analyzer that finds issues in code with better accuracy and reporting.
    Implements improvements from the enhancement guide.
    """
    
    def __init__(
        self,
        file_service: FileService,
        llm_service: LLMService,
        project_context: Optional[ProjectContext] = None,
        analysis_store: Optional[AnalysisStore] = None
    ):
        self.file_service = file_service
        self.llm_service = llm_service
        self.project_context = project_context
        self.analysis_store = analysis_store
        
        # Statistics
        self.issue_count = 0
        self.files_analyzed = 0
        self.total_tokens = 0
        self.analysis_time = 0
        self.issues_by_type = {}
        self.issues_by_severity = {"critical": 0, "major": 0, "minor": 0, "info": 0}
        
        # Cache for analysis results
        self._cache = {}
    
    def analyze_directory(
        self, 
        directory_path: Path, 
        file_patterns: Optional[List[str]] = None,
        analysis_type: str = "standard",
        min_issues: int = config.MIN_ISSUES_TO_FIND,
        cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all code files in a directory.
        
        Args:
            directory_path: Path to the directory to analyze
            file_patterns: Optional list of file patterns to include
            analysis_type: Type of analysis to perform (standard, security, performance, thorough)
            min_issues: Minimum number of issues to find (enforced in prompt)
            cache: Whether to use cached results for unchanged files
            
        Returns:
            Dictionary mapping file paths to analysis results with structured data
        """
        self._reset_statistics()
        start_time = time.time()
        
        # Get all files in the directory
        files = self.file_service.get_all_files(
            directory_path, 
            include_patterns=file_patterns or ["*.*"]
        )
        
        print(f"Found {len(files)} files to analyze in {directory_path}")
        
        # Analyze each file
        results = {}
        
        # Track total files for progress reporting
        total_files = len(files)
        files_processed = 0
        
        for file_path, content in files.items():
            files_processed += 1
            rel_path = Path(file_path).relative_to(directory_path)
            
            # Calculate file hash for caching
            file_hash = self.file_service.calculate_file_hash(content)
            cache_key = f"{file_path}:{analysis_type}:{min_issues}:{file_hash}"
            
            # Check cache if enabled
            if cache and cache_key in self._cache:
                print(f"[{files_processed}/{total_files}] Using cached analysis for {rel_path}")
                results[file_path] = self._cache[cache_key]
                self._update_statistics(results[file_path])
                continue
            
            print(f"[{files_processed}/{total_files}] Analyzing {rel_path}")
            
            # Get language based on file extension
            language = self.file_service.determine_language(file_path)
            if not language:
                print(f"  Skipping {rel_path} (unknown language)")
                continue
            
            # Get project context for this file if available
            file_context = None
            if self.project_context:
                file_context = self.project_context.get_file_analysis(file_path)
            
            # Perform analysis with the specified type
            analysis_result, tokens_used = self.llm_service.analyze_code(
                code=content,
                language=language,
                file_path=str(rel_path),
                analysis_type=analysis_type,
                min_issues=min_issues,
                context=file_context
            )
            
            # Process the analysis result to ensure it has the expected structure
            structured_result = self._structure_analysis_result(analysis_result, file_path, language)
            
            # Update statistics
            self.files_analyzed += 1
            self.total_tokens += tokens_used
            
            # Store in cache
            self._cache[cache_key] = structured_result
            
            # Add to results
            results[file_path] = structured_result
            
            # Update statistics based on the structured result
            self._update_statistics(structured_result)
            
            # Update project context if available
            if self.project_context:
                self.project_context.update_file_analysis(
                    file_path=file_path,
                    analysis_type=analysis_type,
                    analysis_data=structured_result
                )
            
            # Store analysis in the analysis store if available
            if self.analysis_store:
                self.analysis_store.store_analysis(
                    project=str(directory_path),
                    file_path=file_path,
                    analysis_type=analysis_type,
                    analysis_data=structured_result,
                    issue_count=len(structured_result.get("issues", []))
                )
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.1)
        
        self.analysis_time = time.time() - start_time
        
        print(f"Analysis complete. Found {self.issue_count} issues across {self.files_analyzed} files.")
        print(f"Total analysis time: {self.analysis_time:.2f} seconds")
        
        return results
    
    def analyze_file(
        self, 
        file_path: Path, 
        analysis_type: str = "standard",
        min_issues: int = config.MIN_ISSUES_TO_FIND
    ) -> Dict[str, Any]:
        """
        Analyze a single file.
        
        Args:
            file_path: Path to the file to analyze
            analysis_type: Type of analysis to perform
            min_issues: Minimum number of issues to find
            
        Returns:
            Structured analysis result
        """
        # Get file content and language
        content, language = self.file_service.get_file_content(file_path)
        
        if not content or not language:
            print(f"Error: Could not read file {file_path}")
            return {"error": f"Could not read file {file_path}"}
        
        # Get project context for this file if available
        file_context = None
        if self.project_context:
            file_context = self.project_context.get_file_analysis(str(file_path))
        
        # Perform analysis
        analysis_result, tokens_used = self.llm_service.analyze_code(
            code=content,
            language=language,
            file_path=str(file_path),
            analysis_type=analysis_type,
            min_issues=min_issues,
            context=file_context
        )
        
        # Structure result
        structured_result = self._structure_analysis_result(analysis_result, str(file_path), language)
        
        # Update statistics
        self.files_analyzed += 1
        self.total_tokens += tokens_used
        self._update_statistics(structured_result)
        
        # Update project context if available
        if self.project_context:
            self.project_context.update_file_analysis(
                file_path=str(file_path),
                analysis_type=analysis_type,
                analysis_data=structured_result
            )
        
        return structured_result
    
    def _structure_analysis_result(
        self, 
        analysis_result: str, 
        file_path: str, 
        language: str
    ) -> Dict[str, Any]:
        """
        Structure the analysis result to ensure it has the expected format.
        
        Args:
            analysis_result: Raw analysis result from LLM
            file_path: Path to the analyzed file
            language: Language of the analyzed file
            
        Returns:
            Structured analysis result
        """
        # Check if the result is already in a structured format (JSON)
        try:
            # Try to parse as JSON first
            if analysis_result.strip().startswith("{") and analysis_result.strip().endswith("}"):
                structured = json.loads(analysis_result)
                
                # Ensure the required fields are present
                if "summary" not in structured:
                    structured["summary"] = "Analysis summary not provided"
                if "issues" not in structured:
                    structured["issues"] = []
                
                return structured
        except json.JSONDecodeError:
            # If it's not valid JSON, parse as text
            pass
        
        # Extract summary and issues from text-based analysis
        structured = {
            "file_path": file_path,
            "language": language,
            "summary": "",
            "issues": [],
            "suggestions": []
        }
        
        # Extract summary (between "## Summary" and the next section)
        summary_match = re.search(r"#+\s*Summary\s*\n+(.*?)(?=\n#+\s*|$)", analysis_result, re.DOTALL)
        if summary_match:
            structured["summary"] = summary_match.group(1).strip()
        
        # Extract issues
        issue_pattern = r"#+\s*Issue #(\d+)(?:\s*\(Lines?(?:\s+(\d+)(?:-(\d+))?)?\))?\s*:?\s*(.*?)(?=\n#+\s*Issue #\d+|\n#+\s*[^I]|$)"
        for match in re.finditer(issue_pattern, analysis_result, re.DOTALL):
            issue_number = int(match.group(1))
            start_line = int(match.group(2)) if match.group(2) else None
            end_line = int(match.group(3)) if match.group(3) else start_line
            title_and_description = match.group(4).strip()
            
            # Try to separate title from description
            title_lines = title_and_description.split("\n", 1)
            title = title_lines[0].strip()
            description = title_lines[1].strip() if len(title_lines) > 1 else ""
            
            # Determine severity based on keywords
            severity = "minor"  # Default
            if re.search(r"\b(critical|severe|serious|crash|security|exploit|vulnerability)\b", title.lower()):
                severity = "critical"
            elif re.search(r"\b(major|important|significant|error|bug)\b", title.lower()):
                severity = "major"
            elif re.search(r"\b(minor|style|formatting|suggestion|improvement)\b", title.lower()):
                severity = "minor"
            
            # Determine type based on keywords
            issue_type = "general"
            if re.search(r"\b(security|vulnerability|exploit|injection|xss)\b", title.lower()):
                issue_type = "security"
            elif re.search(r"\b(performance|slow|speed|memory|cpu|efficient)\b", title.lower()):
                issue_type = "performance"
            elif re.search(r"\b(maintainability|readability|clarity|documentation)\b", title.lower()):
                issue_type = "maintainability"
            elif re.search(r"\b(bug|error|exception|crash|incorrect)\b", title.lower()):
                issue_type = "bug"
            
            issue = {
                "id": issue_number,
                "title": title,
                "description": description,
                "line_start": start_line,
                "line_end": end_line,
                "severity": severity,
                "type": issue_type,
                "fixed": False
            }
            
            structured["issues"].append(issue)
        
        # Extract suggestions
        suggestion_pattern = r"#+\s*Suggestion(?:\s*#(\d+))?\s*:?\s*(.*?)(?=\n#+\s*Suggestion|\n#+\s*[^S]|$)"
        for match in re.finditer(suggestion_pattern, analysis_result, re.DOTALL):
            suggestion_number = int(match.group(1)) if match.group(1) else len(structured["suggestions"]) + 1
            suggestion_text = match.group(2).strip()
            
            suggestion = {
                "id": suggestion_number,
                "text": suggestion_text
            }
            
            structured["suggestions"].append(suggestion)
        
        return structured
    
    def _update_statistics(self, result: Dict[str, Any]) -> None:
        """
        Update statistics based on an analysis result.
        
        Args:
            result: Structured analysis result
        """
        issues = result.get("issues", [])
        self.issue_count += len(issues)
        
        # Update issue type counts
        for issue in issues:
            issue_type = issue.get("type", "general")
            self.issues_by_type[issue_type] = self.issues_by_type.get(issue_type, 0) + 1
            
            # Update severity counts
            severity = issue.get("severity", "minor")
            self.issues_by_severity[severity] = self.issues_by_severity.get(severity, 0) + 1
    
    def _reset_statistics(self) -> None:
        """Reset statistics for a new analysis run."""
        self.issue_count = 0
        self.files_analyzed = 0
        self.total_tokens = 0
        self.analysis_time = 0
        self.issues_by_type = {}
        self.issues_by_severity = {"critical": 0, "major": 0, "minor": 0, "info": 0}
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the analysis.
        
        Returns:
            Dictionary with analysis statistics
        """
        return {
            "files_analyzed": self.files_analyzed,
            "issue_count": self.issue_count,
            "issues_by_type": self.issues_by_type,
            "issues_by_severity": self.issues_by_severity,
            "total_tokens": self.total_tokens,
            "analysis_time": self.analysis_time
        }
    
    def extract_section(self, analysis_result: Dict[str, Any], section: str) -> str:
        """
        Extract a specific section from a structured analysis result.
        
        Args:
            analysis_result: Structured analysis result
            section: Section to extract (summary, issues, suggestions)
            
        Returns:
            Extracted section as a formatted string
        """
        if section == "summary":
            return analysis_result.get("summary", "No summary available")
        
        elif section == "issues":
            issues = analysis_result.get("issues", [])
            if not issues:
                return "No issues found"
            
            result = []
            for issue in issues:
                location = ""
                if issue.get("line_start"):
                    if issue.get("line_end") and issue["line_end"] != issue["line_start"]:
                        location = f" (Lines {issue['line_start']}-{issue['line_end']})"
                    else:
                        location = f" (Line {issue['line_start']})"
                
                result.append(f"Issue #{issue['id']}{location}: {issue['title']}")
                result.append(f"Severity: {issue['severity'].capitalize()}, Type: {issue['type'].capitalize()}")
                result.append(issue.get("description", ""))
                result.append("")
            
            return "\n".join(result)
        
        elif section == "suggestions":
            suggestions = analysis_result.get("suggestions", [])
            if not suggestions:
                return "No suggestions provided"
            
            result = []
            for suggestion in suggestions:
                result.append(f"Suggestion #{suggestion['id']}: {suggestion['text']}")
                result.append("")
            
            return "\n".join(result)
        
        return f"Unknown section: {section}"
