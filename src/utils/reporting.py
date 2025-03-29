"""
Reporting - Generates reports
"""
from typing import Dict, List, Any
import json
import time

class ReportGenerator:
    """
    Generates reports from analysis results.
    """
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a report from analysis results.
        
        Args:
            results: Analysis results
            
        Returns:
            Report as a string
        """
        # Get basic info
        project_name = results.get("project_name", "Unknown Project")
        timestamp = results.get("analysis_timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
        files_analyzed = results.get("files_analyzed", 0)
        total_issues = results.get("total_issues", 0)
        
        # Start building the report
        report = [
            f"# Code Analysis Report: {project_name}",
            f"\nGenerated on: {timestamp}",
            f"\n## Summary",
            f"\n- **Files Analyzed**: {files_analyzed}",
            f"- **Total Issues Found**: {total_issues}",
        ]
        
        # Add execution stats if available
        execution_time = results.get("execution_time")
        if execution_time:
            report.append(f"- **Execution Time**: {execution_time:.2f} seconds")
        
        avg_time = results.get("average_time_per_file")
        if avg_time:
            report.append(f"- **Average Time Per File**: {avg_time:.2f} seconds")
        
        # Add project-level analysis
        project_analysis = results.get("project_level_analysis")
        if project_analysis:
            report.append(f"\n## Project-Level Analysis\n")
            report.append(project_analysis)
        
        # Add security overview
        security_overview = results.get("security_overview")
        if security_overview:
            report.append(f"\n## Security Overview\n")
            report.append(security_overview)
        
        # Add growth recommendations
        growth_recs = results.get("growth_recommendations", [])
        if growth_recs:
            report.append(f"\n## Growth Recommendations\n")
            for i, rec in enumerate(growth_recs, 1):
                title = rec.get("title", f"Recommendation {i}")
                description = rec.get("description", "No description provided.")
                report.append(f"### {i}. {title}\n")
                report.append(f"{description}\n")
        
        # Add file-level analyses
        file_analyses = results.get("file_analyses", {})
        if file_analyses:
            report.append(f"\n## File Analyses\n")
            
            # Sort files by issue count (descending)
            sorted_files = sorted(
                file_analyses.items(),
                key=lambda x: x[1].get("issue_count", 0),
                reverse=True
            )
            
            # Add each file's analysis
            for file_path, analysis in sorted_files:
                # Get file info
                issue_count = analysis.get("issue_count", 0)
                language = analysis.get("language", "unknown")
                
                # Add file header
                report.append(f"### File: {file_path}")
                report.append(f"- **Language**: {language}")
                report.append(f"- **Issues**: {issue_count}")
                
                # Add issues
                issues = analysis.get("issues", [])
                if issues:
                    report.append("\n#### Issues Found:\n")
                    for i, issue in enumerate(issues, 1):
                        line_info = f"(Line {issue.get('line_number')})" if issue.get('line_number') else ""
                        description = issue.get("description", "No description provided.")
                        report.append(f"{i}. **Issue {line_info}**: {description}")
                
                # Add newline between files
                report.append("\n")
        
        # Join the report parts
        return "\n".join(report)
    
    def generate_json_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a JSON report from analysis results.
        
        Args:
            results: Analysis results
            
        Returns:
            Report as a JSON string
        """
        return json.dumps(results, indent=2)
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a summary report from analysis results.
        
        Args:
            results: Analysis results
            
        Returns:
            Summary report as a string
        """
        # Get basic info
        project_name = results.get("project_name", "Unknown Project")
        timestamp = results.get("analysis_timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
        files_analyzed = results.get("files_analyzed", 0)
        total_issues = results.get("total_issues", 0)
        
        # Start building the report
        report = [
            f"# Code Analysis Summary: {project_name}",
            f"\nGenerated on: {timestamp}",
            f"\n## Summary",
            f"\n- **Files Analyzed**: {files_analyzed}",
            f"- **Total Issues Found**: {total_issues}",
        ]
        
        # Count issues by severity if available
        severity_counts = {
            "High": 0,
            "Medium": 0,
            "Low": 0
        }
        
        file_analyses = results.get("file_analyses", {})
        for file_path, analysis in file_analyses.items():
            issues = analysis.get("issues", [])
            for issue in issues:
                severity = issue.get("severity", "Medium")
                if severity in severity_counts:
                    severity_counts[severity] += 1
        
        report.append("\n### Issues by Severity")
        for severity, count in severity_counts.items():
            if count > 0:
                report.append(f"- **{severity}**: {count}")
        
        # Add top issues (if available)
        project_analysis = results.get("project_level_analysis")
        if project_analysis:
            report.append(f"\n## Key Findings")
            # Extract a summary (first paragraph) from the project analysis
            paragraphs = project_analysis.split('\n\n')
            if paragraphs:
                report.append(paragraphs[0])
                report.append("\n[See full report for details]")
        
        # Add security summary if available
        security_overview = results.get("security_overview")
        if security_overview:
            report.append(f"\n## Security Summary")
            # Extract the first paragraph of the security overview
            paragraphs = security_overview.split('\n\n')
            if paragraphs:
                report.append(paragraphs[0])
                report.append("\n[See full report for details]")
        
        # Add top growth recommendations
        growth_recs = results.get("growth_recommendations", [])
        if growth_recs and len(growth_recs) > 0:
            report.append(f"\n## Top Growth Recommendation")
            rec = growth_recs[0]
            title = rec.get("title", "Growth Recommendation")
            report.append(f"### {title}")
            # Extract a shorter version of the description
            description = rec.get("description", "")
            short_desc = description.split('\n\n')[0] if description else ""
            report.append(short_desc)
            report.append("\n[See full report for more recommendations]")
        
        # Join the report parts
        return "\n".join(report)