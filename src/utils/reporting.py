#!/usr/bin/env python3
"""
Reporting - Generates human-readable reports from analysis results
"""
from typing import Dict, List, Any, Optional
import os
import time

class ReportGenerator:
    """
    Generates human-readable reports from analysis results.
    """
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a markdown report from analysis results.
        
        Args:
            results: Analysis results
            
        Returns:
            Markdown report as a string
        """
        # Create report header
        report = f"# Code Analysis Report: {results['project_name']}\n\n"
        
        # Add summary section
        report += "## Summary\n\n"
        report += f"* **Date:** {results['analysis_timestamp']}\n"
        report += f"* **Files Analyzed:** {results['files_analyzed']}\n"
        report += f"* **Total Issues Found:** {results['total_issues']}\n"
        report += f"* **Analysis Time:** {results.get('execution_time', 0):.2f} seconds\n\n"
        
        # Add executive summary section
        if results.get('project_level_analysis'):
            report += "## Executive Summary\n\n"
            report += f"{results['project_level_analysis']}\n\n"
        
        # Add security overview section
        if results.get('security_overview'):
            report += "## Security Overview\n\n"
            report += f"{results['security_overview']}\n\n"
            
        # Add growth recommendations section
        if results.get('growth_recommendations'):
            report += "## Growth Recommendations\n\n"
            for i, rec in enumerate(results['growth_recommendations'], 1):
                report += f"### {i}. {rec.get('title', 'Recommendation')}\n\n"
                report += f"{rec.get('description', '')}\n\n"
        
        # Add file analyses
        report += "## File Analysis\n\n"
        
        # Sort files based on issue count
        file_analyses = results.get('file_analyses', {})
        sorted_files = sorted(
            file_analyses.items(), 
            key=lambda x: x[1].get('issue_count', 0), 
            reverse=True
        )
        
        for file_path, analysis in sorted_files:
            # Skip files with no issues
            if analysis.get('issue_count', 0) == 0:
                continue
                
            # Add file header
            report += f"## File: {file_path}\n\n"
            
            # Add file info
            if analysis.get('file_info'):
                file_info = analysis['file_info']
                report += f"* **Language:** {analysis.get('language', 'Unknown')}\n"
                report += f"* **Size:** {file_info.get('size', 0):,} bytes\n"
                report += f"* **Issues Found:** {analysis.get('issue_count', 0)}\n\n"
            
            # Add issues
            if analysis.get('issues'):
                for i, issue in enumerate(analysis['issues'], 1):
                    # Line number text
                    line_text = ""
                    if issue.get('line_number'):
                        line_text = f" (Line {issue['line_number']})"
                        
                    # Add issue
                    report += f"### Issue #{i}{line_text}: {issue.get('description', '')}\n\n"
        
        return report
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a short summary report from analysis results.
        
        Args:
            results: Analysis results
            
        Returns:
            Markdown summary report as a string
        """
        # Create report header
        report = f"# Code Analysis Summary: {results['project_name']}\n\n"
        
        # Add summary section
        report += "## Overview\n\n"
        report += f"* **Date:** {results['analysis_timestamp']}\n"
        report += f"* **Files Analyzed:** {results['files_analyzed']}\n"
        report += f"* **Total Issues Found:** {results['total_issues']}\n"
        
        # Add statistics based on issue type/severity
        issue_types = {'security': 0, 'performance': 0, 'quality': 0, 'other': 0}
        issue_severity = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        
        for _, analysis in results.get('file_analyses', {}).items():
            if 'issues' in analysis:
                for issue in analysis['issues']:
                    # Categorize issue type based on description
                    desc = issue.get('description', '').lower()
                    
                    # Count by type
                    if any(word in desc for word in ['security', 'vulnerability', 'hack', 'inject', 'auth']):
                        issue_types['security'] += 1
                    elif any(word in desc for word in ['performance', 'slow', 'memory', 'cpu', 'optimiz']):
                        issue_types['performance'] += 1
                    elif any(word in desc for word in ['quality', 'standard', 'best practice', 'code style']):
                        issue_types['quality'] += 1
                    else:
                        issue_types['other'] += 1
                    
                    # Count by severity (based on language used)
                    if any(word in desc for word in ['critical', 'severe', 'urgent', 'security']):
                        issue_severity['high'] += 1
                    elif any(word in desc for word in ['important', 'significant', 'moderate']):
                        issue_severity['medium'] += 1
                    elif any(word in desc for word in ['minor', 'cosmetic', 'style', 'typo']):
                        issue_severity['low'] += 1
                    else:
                        issue_severity['unknown'] += 1
        
        # Add issue breakdown
        report += "\n## Issue Breakdown\n\n"
        report += "### By Type\n\n"
        for itype, count in issue_types.items():
            if count > 0:
                report += f"* **{itype.capitalize()}:** {count}\n"
                
        report += "\n### By Severity\n\n"
        for severity, count in issue_severity.items():
            if count > 0:
                report += f"* **{severity.capitalize()}:** {count}\n"
        
        # Add top files by issues
        file_analyses = results.get('file_analyses', {})
        if file_analyses:
            sorted_files = sorted(
                file_analyses.items(), 
                key=lambda x: x[1].get('issue_count', 0), 
                reverse=True
            )[:5]  # Top 5 files
            
            if sorted_files:
                report += "\n## Top Files by Issues\n\n"
                for file_path, analysis in sorted_files:
                    if analysis.get('issue_count', 0) > 0:
                        report += f"* **{os.path.basename(file_path)}:** {analysis.get('issue_count', 0)} issues\n"
        
        return report