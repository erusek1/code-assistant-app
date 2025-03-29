#!/usr/bin/env python3
"""
Code Assistant - A tool for analyzing and fixing code
"""
import argparse
import sys
import os
from pathlib import Path

from src.analyzer.code_analyzer import CodeAnalyzer
from src.fixer.code_fixer import CodeFixer
from src.memory.analysis_store import AnalysisStore
from src.memory.project_context import ProjectContext
from src.llm.llm_service import LLMService
from src.utils.file_service import FileService
from src.utils.reporting import ReportGenerator
import config

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Code Assistant - Analyze and fix code")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code in a directory")
    analyze_parser.add_argument("path", type=str, help="Path to the directory to analyze")
    analyze_parser.add_argument("--fresh", action="store_true", help="Perform a fresh analysis without using previous context")
    analyze_parser.add_argument("--output", type=str, help="Path to save the analysis report", default="analysis_report.md")
    
    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Fix issues based on previous analysis")
    fix_parser.add_argument("path", type=str, help="Path to the directory to fix")
    fix_parser.add_argument("--analysis", type=str, help="Path to the analysis file to use", default="analysis_report.md")
    fix_parser.add_argument("--output-dir", type=str, help="Directory to save fixed files", default="fixed_files")
    
    # List analyses command
    list_parser = subparsers.add_parser("list", help="List available analyses")
    
    return parser.parse_args()

def analyze_command(args):
    """Execute the analyze command."""
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path '{path}' does not exist")
        return 1
    
    # Initialize services
    file_service = FileService()
    llm_service = LLMService(
        analysis_model=config.ANALYSIS_MODEL,
        chat_model=config.CHAT_MODEL
    )
    
    # Initialize project context and analysis store
    if args.fresh:
        # For fresh analysis, create new context
        project_context = ProjectContext(project_path=path)
        analysis_store = AnalysisStore(store_path=config.ANALYSIS_STORE_PATH)
    else:
        # Load existing context if available
        project_context = ProjectContext.load_or_create(
            project_path=path,
            context_path=config.PROJECT_CONTEXT_PATH
        )
        analysis_store = AnalysisStore(store_path=config.ANALYSIS_STORE_PATH)
        
    # Initialize analyzer
    analyzer = CodeAnalyzer(
        file_service=file_service,
        llm_service=llm_service,
        project_context=project_context,
        analysis_store=analysis_store
    )
    
    # Perform analysis
    print(f"Analyzing code in: {path}")
    results = analyzer.analyze_directory(path)
    
    # Generate report
    report_generator = ReportGenerator()
    report = report_generator.generate_report(results)
    
    # Save report
    with open(args.output, "w") as f:
        f.write(report)
    
    print(f"Analysis complete. Found {analyzer.issue_count} issues across {analyzer.files_analyzed} files.")
    print(f"Report saved to: {args.output}")
    
    # Save context for future use
    project_context.save(config.PROJECT_CONTEXT_PATH)
    
    return 0

def fix_command(args):
    """Execute the fix command."""
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path '{path}' does not exist")
        return 1
    
    analysis_path = Path(args.analysis)
    if not analysis_path.exists():
        print(f"Error: Analysis file '{analysis_path}' does not exist")
        return 1
    
    # Initialize services
    file_service = FileService()
    llm_service = LLMService(
        analysis_model=config.ANALYSIS_MODEL,
        chat_model=config.CHAT_MODEL
    )
    
    # Load project context
    project_context = ProjectContext.load_or_create(
        project_path=path,
        context_path=config.PROJECT_CONTEXT_PATH
    )
    
    # Initialize code fixer
    fixer = CodeFixer(
        file_service=file_service,
        llm_service=llm_service,
        project_context=project_context
    )
    
    # Load analysis report
    with open(analysis_path, "r") as f:
        analysis_report = f.read()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Fix issues
    print(f"Fixing issues based on analysis in: {analysis_path}")
    fixed_files = fixer.fix_from_analysis(analysis_report, path)
    
    # Save fixed files
    for file_path, fixed_content in fixed_files.items():
        rel_path = Path(file_path).relative_to(path)
        output_path = output_dir / rel_path
        
        # Create parent directories if they don't exist
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Write fixed file
        with open(output_path, "w") as f:
            f.write(fixed_content)
    
    print(f"Fixed {len(fixed_files)} files. Saved to: {output_dir}")
    return 0

def list_command(args):
    """List available analyses."""
    analysis_store = AnalysisStore(store_path=config.ANALYSIS_STORE_PATH)
    analyses = analysis_store.list_analyses()
    
    if not analyses:
        print("No analyses found.")
        return 0
    
    print(f"Found {len(analyses)} analyses:")
    for analysis in analyses:
        print(f" - {analysis['project']}: {analysis['timestamp']} ({analysis['issue_count']} issues)")
    
    return 0

def main():
    """Main entry point."""
    args = parse_arguments()
    
    if args.command == "analyze":
        return analyze_command(args)
    elif args.command == "fix":
        return fix_command(args)
    elif args.command == "list":
        return list_command(args)
    else:
        print("Please specify a command. Use --help for more information.")
        return 1

if __name__ == "__main__":
    sys.exit(main())