"""
Prompt Builder - Creates effective prompts for LLM interactions
"""
from typing import Dict, List, Any, Optional
import json
import os

import config

class PromptBuilder:
    """
    Creates effective prompts for different LLM interactions.
    """
    
    def build_analysis_prompt(
        self,
        code: str,
        language: str,
        file_path: str,
        analysis_type: str = "standard"
    ) -> str:
        """
        Build a prompt for code analysis.
        
        Args:
            code: Code to analyze
            language: Programming language
            file_path: Path to the file
            analysis_type: Type of analysis to perform
            
        Returns:
            Prompt for code analysis
        """
        # Base system prompt
        system_prompt = f"""You are an expert code reviewer and developer with years of experience in {language}.
You are highly critical and thorough, always finding issues even in well-written code.
You're analyzing a file: {file_path}

Your task is to perform a {analysis_type} analysis of the following code.
"""

        # Add specific instructions based on analysis type
        if analysis_type == "standard":
            system_prompt += """
Focus on:
1. Code quality and best practices
2. Potential bugs and edge cases
3. Design patterns and architecture
4. Code organization and readability
5. Performance considerations
6. Error handling and robustness

You MUST find at least 2-3 issues, even in well-written code. Nothing is perfect.
"""
        elif analysis_type == "security":
            system_prompt += """
Focus on SECURITY issues only:
1. Potential vulnerabilities
2. Input validation and sanitization
3. Authentication and authorization issues
4. Data exposure risks
5. Injection attacks
6. Secure coding practices
7. Dependencies with known vulnerabilities
8. Hardcoded secrets or credentials

You MUST find at least 2 security concerns, even if they're minor. All code has security implications.
"""
        elif analysis_type == "performance":
            system_prompt += """
Focus on PERFORMANCE issues only:
1. Algorithms and data structures efficiency
2. Resource usage (memory, CPU, I/O)
3. Bottlenecks and optimization opportunities
4. Caching and memoization
5. Batching and parallel processing
6. Database queries and operations
7. Network calls and external service interactions

You MUST find at least 2 performance concerns, even if they're minor. All code can be optimized.
"""
        elif analysis_type == "growth":
            system_prompt += """
Focus on GROWTH and SCALABILITY issues only:
1. Architectural limitations
2. Hardcoded constraints or limitations
3. Opportunities for extensibility
4. Modularization and component isolation
5. Opportunities for service-oriented design
6. Load handling and scaling considerations
7. Dependency management and coupling

You MUST find at least 2 growth or scalability concerns. Think about future expansion.
"""
        
        # Add formatting instructions
        system_prompt += """
FORMAT YOUR RESPONSE:
1. Line numbers MUST be specified for each issue
2. Each issue MUST have a clear description
3. Each issue MUST include a specific, actionable recommendation
4. Be direct and specific - don't use phrases like "you might want to" or "consider"
5. Use Markdown formatting for clarity

Example:
### Issue #1 (Lines 25-28):
The error handling is insufficient. The catch block silently ignores errors, which makes debugging difficult.

### Recommendation:
Add proper logging in the catch block and either rethrow or handle the error explicitly.
"""

        # Add urgency to ensure issues are found
        system_prompt += f"""
IMPORTANT: If you cannot find at least {config.MIN_ISSUES_TO_FIND} issues, you are not looking hard enough.
Even professionally written code has issues. Be critical!
"""

        # Construct the full prompt
        prompt = f"{system_prompt}\n\n```{language}\n{code}\n```\n\nProvide your {analysis_type} analysis:"
        
        return prompt
    
    def build_fix_prompt(
        self,
        code: str,
        language: str,
        file_path: str,
        issues: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> str:
        """
        Build a prompt for fixing code issues.
        
        Args:
            code: Code to fix
            language: Programming language
            file_path: Path to the file
            issues: List of issues to fix
            context: Additional context for fixing
            
        Returns:
            Prompt for fixing code
        """
        # Prepare issues text
        issues_text = ""
        for i, issue in enumerate(issues, 1):
            line_info = f"(Line {issue['line_number']})" if issue.get('line_number') else ""
            issues_text += f"### Issue #{i} {line_info}:\n{issue['description']}\n\n"
        
        # Base system prompt
        system_prompt = f"""You are an expert code fixer and developer specializing in {language}.
You have been asked to fix issues in a file: {file_path}

Your task is to fix the following issues while preserving the functionality and intent of the code.
"""

        # Add context if provided
        if context:
            system_prompt += f"\nContext about the codebase:\n{context}\n"
        
        # Add specific instructions
        system_prompt += """
IMPORTANT INSTRUCTIONS:
1. Do NOT remove functionality or change the overall behavior
2. Make the minimal necessary changes to fix each issue
3. Follow best practices for the language
4. Ensure your fixes are complete and correct
5. Return the ENTIRE fixed file, not just the changed sections
6. Add brief comments explaining your fixes
7. Do not introduce new issues
"""
        
        # Add issue reminder
        if len(issues) == 1:
            system_prompt += "\nRemember you are fixing exactly 1 issue."
        else:
            system_prompt += f"\nRemember you are fixing {len(issues)} issues."
        
        # Construct the full prompt
        prompt = f"{system_prompt}\n\nISSUES TO FIX:\n{issues_text}\n\nORIGINAL CODE:\n```{language}\n{code}\n```\n\nFIXED CODE:"
        
        return prompt
    
    def build_project_analysis_prompt(
        self,
        project_name: str,
        project_structure: Dict[str, Any],
        file_count: int,
        issue_count: int,
        top_issues: List[tuple],
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Build a prompt for project-level analysis.
        
        Args:
            project_name: Name of the project
            project_structure: Structure of the project
            file_count: Number of files analyzed
            issue_count: Number of issues found
            top_issues: Top issues found
            file_analyses: Analyses of individual files
            
        Returns:
            Prompt for project-level analysis
        """
        # Convert project structure to string
        structure_str = json.dumps(project_structure, indent=2)
        
        # Prepare top issues text
        top_issues_text = ""
        for i, (issue, count) in enumerate(top_issues, 1):
            top_issues_text += f"{i}. {issue} (found in {count} files)\n"
        
        # Base system prompt
        system_prompt = f"""You are an expert software architect and technical lead.
You are analyzing a project called '{project_name}' as a whole.

PROJECT OVERVIEW:
- Files analyzed: {file_count}
- Total issues found: {issue_count}
- Project structure: {structure_str}

TOP ISSUES:
{top_issues_text}

Your task is to provide a comprehensive project-level analysis.
"""

        # Add specific instructions
        system_prompt += """
Focus on:
1. Overall code quality and architecture
2. Common patterns of issues across files
3. Potential architectural improvements
4. Technical debt assessment
5. Recommendations for refactoring
6. Prioritization of fixes (what should be fixed first)
7. Growth potential and scalability

FORMAT YOUR RESPONSE:
1. Start with an Executive Summary (2-3 paragraphs)
2. Provide sections for each major area of concern
3. Include concrete, actionable recommendations
4. Use Markdown formatting for readability
5. Be specific and direct in your assessment
"""

        # Construct the full prompt
        prompt = f"{system_prompt}\n\nProject-level analysis:"
        
        return prompt
    
    def build_growth_recommendations_prompt(
        self,
        project_name: str,
        project_structure: Dict[str, Any],
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Build a prompt for generating growth recommendations.
        
        Args:
            project_name: Name of the project
            project_structure: Structure of the project
            file_analyses: Analyses of individual files
            
        Returns:
            Prompt for generating growth recommendations
        """
        # Convert project structure to string
        structure_str = json.dumps(project_structure, indent=2)
        
        # Base system prompt
        system_prompt = f"""You are an expert software architect and technical lead with a focus on scalable enterprise applications.
You are analyzing a project called '{project_name}' to provide growth and scalability recommendations.

Your goal is to help transform this codebase into an enterprise-grade application (similar to QuickBooks scale).

PROJECT OVERVIEW:
- Project structure: {structure_str}

Your task is to provide detailed growth recommendations.

Focus on:
1. Scaling architecture for enterprise use
2. Potential microservices or service-oriented architecture
3. Database and data storage scalability
4. Security at scale
5. Multi-user support and access control
6. Deployment and DevOps considerations
7. Testing and quality assurance at scale
8. Monitoring, logging, and observability
9. Performance optimization for large datasets
10. Integration with enterprise systems

FORMAT YOUR RESPONSE:
1. Provide 5-7 specific growth recommendations
2. For each recommendation:
   - Provide a clear title
   - Explain why it's important for enterprise scale
   - Describe how to implement it
   - Mention potential challenges
3. Sort recommendations by priority
4. Be specific and direct

IMPORTANT: Focus on transformative, enterprise-level changes. Think big - how can this codebase support
thousands of users, millions of transactions, and enterprise-grade reliability and security?
"""

        # Construct the full prompt
        prompt = f"{system_prompt}\n\nGrowth recommendations:"
        
        return prompt
    
    def build_security_overview_prompt(
        self,
        project_name: str,
        security_issues: List[Dict[str, Any]],
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Build a prompt for generating a security overview.
        
        Args:
            project_name: Name of the project
            security_issues: Security issues found
            file_analyses: Analyses of individual files
            
        Returns:
            Prompt for generating a security overview
        """
        # Prepare security issues text
        security_issues_text = ""
        for i, issue in enumerate(security_issues, 1):
            file_info = f"(in {issue.get('file', 'unknown file')})" if issue.get('file') else ""
            line_info = f"(Line {issue.get('line_number')})" if issue.get('line_number') else ""
            security_issues_text += f"{i}. {issue.get('description')} {file_info} {line_info}\n"
        
        # Base system prompt
        system_prompt = f"""You are an expert security consultant specializing in application security.
You are conducting a security audit of a project called '{project_name}'.

SECURITY ISSUES FOUND:
{security_issues_text if security_issues_text else "No specific security issues were identified, but this does not mean the code is secure."}

Your task is to provide a comprehensive security overview of the project.
"""

        # Add specific instructions
        system_prompt += """
Focus on:
1. Overall security posture
2. Potential vulnerabilities not specifically identified
3. Security architecture recommendations
4. Authentication and authorization
5. Data protection
6. Secure coding practices
7. Dependency management
8. Security testing recommendations

FORMAT YOUR RESPONSE:
1. Start with an Executive Summary of security status
2. Provide a Risk Assessment (High/Medium/Low) with justification
3. List specific security concerns and recommendations
4. Include a section on "Security Roadmap" for future improvements
5. Use Markdown formatting for readability
"""
        
        # Construct the full prompt
        prompt = f"{system_prompt}\n\nSecurity overview:"
        
        return prompt
    
    def build_chat_prompt(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> str:
        """
        Build a prompt for chat interaction.
        
        Args:
            message: User message
            conversation_history: Previous conversation history
            context: Additional context for the conversation
            
        Returns:
            Prompt for chat interaction
        """
        # Base system prompt
        system_prompt = """You are a helpful, knowledgeable, and professional coding assistant.
You help users understand, create, and improve their code.
You provide clear, concise, and accurate information.
"""

        # Add context if provided
        if context:
            system_prompt += f"\nRELEVANT CONTEXT:\n{context}\n"
        
        # Add specific instructions
        system_prompt += """
When answering:
1. Be direct and to the point
2. Provide code examples when helpful
3. Explain complex concepts clearly
4. If you don't know something, say so
5. Follow best practices for code
"""
        
        # Construct conversation history
        convo_text = ""
        for entry in conversation_history:
            if entry.get("role") == "user":
                convo_text += f"User: {entry.get('content')}\n\n"
            elif entry.get("role") == "assistant":
                convo_text += f"Assistant: {entry.get('content')}\n\n"
        
        # Construct the full prompt
        prompt = f"{system_prompt}\n\nCONVERSATION HISTORY:\n{convo_text}\nUser: {message}\n\nAssistant:"
        
        return prompt