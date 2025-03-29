"""
Code Analyzer - Analyzes code and identifies issues
"""
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from src.llm.llm_service import LLMService
from src.utils.file_service import FileService
from src.memory.analysis_store import AnalysisStore
from src.memory.project_context import ProjectContext
import config

class CodeAnalyzer:
    """
    Analyzes code for issues and provides recommendations for fixes.
    """
    
    def __init__(
        self,
        file_service: FileService,
        llm_service: LLMService,
        project_context: ProjectContext,
        analysis_store: AnalysisStore
    ):
        self.file_service = file_service
        self.llm_service = llm_service
        self.project_context = project_context
        self.analysis_store = analysis_store
        
        # Statistics
        self.issue_count = 0
        self.files_analyzed = 0
        self.start_time = None
        self.total_tokens = 0
    
    def analyze_directory(self, directory_path: Path) -> Dict[str, Any]:
        """
        Analyze all code files in a directory recursively.
        
        Args:
            directory_path: Path to the directory to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        self.issue_count = 0
        self.files_analyzed = 0
        self.start_time = time.time()
        self.total_tokens = 0
        
        # Get all files to analyze
        files = self.file_service.get_code_files(directory_path)
        
        if not files:
            print(f"No files to analyze in {directory_path}")
            return {"error": "No files to analyze"}
        
        # Initialize results dictionary
        results = {
            "project_name": directory_path.name,
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files_analyzed": len(files),
            "total_issues": 0,
            "file_analyses": {},
            "project_level_analysis": None,
            "growth_recommendations": [],
            "security_overview": None,
        }
        
        # Analyze each file
        print(f"Analyzing {len(files)} files...")
        
        for i, file_path in enumerate(files):
            print(f"[{i+1}/{len(files)}] Analyzing {file_path.relative_to(directory_path)}")
            
            # Get file content and language
            content, language = self.file_service.get_file_content(file_path)
            
            if not content or not language:
                continue
                
            # Check if we have an existing analysis for this file
            existing_analysis = self.project_context.get_file_analysis(str(file_path))
            file_modified = self.file_service.is_file_modified(file_path, existing_analysis)
            
            # If file hasn't been modified, use existing analysis
            if existing_analysis and not file_modified:
                print(f"  Using existing analysis for {file_path.name}")
                file_analysis = existing_analysis
                issue_count = self._count_issues(file_analysis)
            else:
                # Perform analysis
                file_analysis = self._analyze_file(file_path, content, language)
                issue_count = self._count_issues(file_analysis)
                
                # Update project context with new analysis
                self.project_context.update_file_analysis(str(file_path), file_analysis)
            
            # Update statistics
            self.issue_count += issue_count
            self.files_analyzed += 1
            
            # Add to results
            results["file_analyses"][str(file_path)] = file_analysis
        
        # Update total issues
        results["total_issues"] = self.issue_count
        
        # Generate project-level analysis
        print("Generating project-level analysis...")
        project_analysis = self._generate_project_analysis(directory_path, results["file_analyses"])
        results["project_level_analysis"] = project_analysis
        
        # Generate growth recommendations
        print("Generating growth recommendations...")
        growth_recs = self._generate_growth_recommendations(directory_path, results["file_analyses"])
        results["growth_recommendations"] = growth_recs
        
        # Generate security overview
        print("Generating security overview...")
        security_overview = self._generate_security_overview(directory_path, results["file_analyses"])
        results["security_overview"] = security_overview
        
        # Add execution statistics
        execution_time = time.time() - self.start_time
        results["execution_time"] = execution_time
        results["average_time_per_file"] = execution_time / len(files) if files else 0
        results["total_tokens"] = self.total_tokens
        
        # Store analysis in the analysis store
        self.analysis_store.store_analysis(
            project_name=directory_path.name,
            results=results
        )
        
        print(f"Analysis complete in {execution_time:.2f} seconds.")
        print(f"Found {self.issue_count} issues across {self.files_analyzed} files.")
        
        return results
    
    def _analyze_file(self, file_path: Path, content: str, language: str) -> Dict[str, Any]:
        """
        Analyze a single file for issues.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            language: Programming language of the file
            
        Returns:
            Dictionary containing analysis results for the file
        """
        # Get file info
        file_info = self.file_service.get_file_info(file_path)
        
        # Perform standard analysis
        analysis_result, tokens_used = self.llm_service.analyze_code(
            code=content,
            language=language,
            file_path=str(file_path),
            analysis_type="standard"
        )
        
        # Perform security analysis if file is complex enough
        security_analysis = None
        if len(content.splitlines()) > 20:  # Only for substantial files
            security_analysis, sec_tokens = self.llm_service.analyze_code(
                code=content,
                language=language,
                file_path=str(file_path),
                analysis_type="security"
            )
            tokens_used += sec_tokens
        
        # Perform performance analysis if file is complex enough
        performance_analysis = None
        if len(content.splitlines()) > 50:  # Only for very substantial files
            performance_analysis, perf_tokens = self.llm_service.analyze_code(
                code=content,
                language=language,
                file_path=str(file_path),
                analysis_type="performance"
            )
            tokens_used += perf_tokens
        
        # Update token count
        self.total_tokens += tokens_used
        
        # Extract issues from analysis
        issues = self._extract_issues(analysis_result)
        security_issues = self._extract_issues(security_analysis) if security_analysis else []
        performance_issues = self._extract_issues(performance_analysis) if performance_analysis else []
        
        # Combine all issues
        all_issues = issues + security_issues + performance_issues
        
        # Create analysis result
        result = {
            "file_path": str(file_path),
            "language": language,
            "file_info": file_info,
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "issues": all_issues,
            "issue_count": len(all_issues),
            "standard_analysis": analysis_result,
            "security_analysis": security_analysis,
            "performance_analysis": performance_analysis,
            "tokens_used": tokens_used,
        }
        
        return result
    
    def _extract_issues(self, analysis_text: Optional[str]) -> List[Dict[str, Any]]:
        """
        Extract issues from analysis text.
        
        Args:
            analysis_text: Text containing analysis
            
        Returns:
            List of issues extracted from the analysis
        """
        if not analysis_text:
            return []
        
        issues = []
        
        # Different patterns to match issues
        patterns = [
            # Match issues with line numbers
            r"(?:Issue|Problem|Bug|Error|Warning)\s+\#?\d*\s*:\s*(.+?)(?:\n|$)",
            r"(?:Line|Lines)\s+(\d+(?:-\d+)?)\s*:\s*(.+?)(?:\n|$)",
            # Match numbered list items
            r"^\s*\d+\.\s*(.+?)(?:\n|$)",
            # Match bullet points
            r"^\s*\*\s*(.+?)(?:\n|$)",
            r"^\s*-\s*(.+?)(?:\n|$)",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, analysis_text, re.MULTILINE)
            for match in matches:
                if len(match.groups()) == 1:
                    # Single group pattern (issue description only)
                    description = match.group(1).strip()
                    line_number = None
                elif len(match.groups()) == 2:
                    # Two group pattern (line number and description)
                    line_number = match.group(1).strip()
                    description = match.group(2).strip()
                else:
                    continue
                
                # Skip if the description is too short
                if len(description) < 10:
                    continue
                
                # Add issue if not already added
                if not any(issue["description"] == description for issue in issues):
                    issues.append({
                        "line_number": line_number,
                        "description": description,
                        "fixed": False,
                    })
        
        # If no issues were found with regex but it's clear there are issues,
        # use a simpler approach: just split by newlines and take non-empty lines
        if not issues and "issue" in analysis_text.lower():
            lines = [line.strip() for line in analysis_text.split("\n") if line.strip()]
            for line in lines:
                if len(line) > 20 and not line.startswith("#") and not line.startswith("```"):
                    issues.append({
                        "line_number": None,
                        "description": line,
                        "fixed": False,
                    })
        
        return issues
    
    def _count_issues(self, file_analysis: Dict[str, Any]) -> int:
        """
        Count the number of issues in a file analysis.
        
        Args:
            file_analysis: Analysis of a file
            
        Returns:
            Number of issues found
        """
        if not file_analysis:
            return 0
            
        if "issues" in file_analysis:
            return len(file_analysis["issues"])
        elif "issue_count" in file_analysis:
            return file_analysis["issue_count"]
        else:
            return 0
    
    def _generate_project_analysis(
        self,
        directory_path: Path,
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate project-level analysis based on individual file analyses.
        
        Args:
            directory_path: Path to the project directory
            file_analyses: Analyses of individual files
            
        Returns:
            Project-level analysis as a string
        """
        # Create project overview
        project_structure = self.file_service.get_project_structure(directory_path)
        file_count = len(file_analyses)
        issue_count = sum(self._count_issues(analysis) for analysis in file_analyses.values())
        
        # Get frequent issues
        all_issues = []
        for analysis in file_analyses.values():
            if "issues" in analysis:
                all_issues.extend(analysis["issues"])
        
        # Count issue frequencies
        issue_frequencies = {}
        for issue in all_issues:
            desc = issue["description"]
            if len(desc) > 200:  # Truncate long descriptions
                desc = desc[:200] + "..."
            issue_frequencies[desc] = issue_frequencies.get(desc, 0) + 1
        
        # Get top issues
        top_issues = sorted(issue_frequencies.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Generate the analysis with the LLM
        project_analysis, tokens = self.llm_service.generate_project_analysis(
            project_name=directory_path.name,
            project_structure=project_structure,
            file_count=file_count,
            issue_count=issue_count,
            top_issues=top_issues,
            file_analyses=file_analyses
        )
        
        self.total_tokens += tokens
        
        return project_analysis
    
    def _generate_growth_recommendations(
        self,
        directory_path: Path,
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate growth recommendations for the project.
        
        Args:
            directory_path: Path to the project directory
            file_analyses: Analyses of individual files
            
        Returns:
            List of growth recommendations
        """
        # Get project structure
        project_structure = self.file_service.get_project_structure(directory_path)
        
        # Generate growth recommendations with the LLM
        growth_recommendations_text, tokens = self.llm_service.generate_growth_recommendations(
            project_name=directory_path.name,
            project_structure=project_structure,
            file_analyses=file_analyses
        )
        
        self.total_tokens += tokens
        
        # Parse recommendations into a structured format
        recommendations = []
        
        # Split by sections or numbered recommendations
        sections = re.split(r"\n\s*\d+\.\s+", growth_recommendations_text)
        if len(sections) > 1:
            # Remove the intro text before the numbered list
            sections = [sections[0]] + ["{}. {}".format(i, section) for i, section in enumerate(sections[1:], 1)]
        
        for section in sections[1:] if len(sections) > 1 else [growth_recommendations_text]:
            # Extract title and description
            lines = section.strip().split("\n")
            title = lines[0].strip()
            description = "\n".join(lines[1:]).strip()
            
            recommendations.append({
                "title": title,
                "description": description,
                "implemented": False,
            })
        
        return recommendations
    
    def _generate_security_overview(
        self,
        directory_path: Path,
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate a security overview for the project.
        
        Args:
            directory_path: Path to the project directory
            file_analyses: Analyses of individual files
            
        Returns:
            Security overview as a string
        """
        # Collect all security issues
        security_issues = []
        for analysis in file_analyses.values():
            if "security_analysis" in analysis and analysis["security_analysis"]:
                issues = self._extract_issues(analysis["security_analysis"])
                if issues:
                    for issue in issues:
                        issue["file"] = analysis["file_path"]
                    security_issues.extend(issues)
        
        # If no security issues were found through dedicated analysis,
        # look for security-related issues in standard analysis
        if not security_issues:
            for analysis in file_analyses.values():
                if "issues" in analysis:
                    for issue in analysis["issues"]:
                        desc = issue["description"].lower()
                        if any(term in desc for term in ["secur", "vulnerab", "inject", "xss", "csrf", "auth", "hack"]):
                            security_issue = issue.copy()
                            security_issue["file"] = analysis["file_path"]
                            security_issues.append(security_issue)
        
        # Generate security overview with the LLM
        security_overview, tokens = self.llm_service.generate_security_overview(
            project_name=directory_path.name,
            security_issues=security_issues,
            file_analyses=file_analyses
        )
        
        self.total_tokens += tokens
        
        return security_overview