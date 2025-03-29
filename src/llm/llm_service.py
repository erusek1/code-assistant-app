"""
LLM Service - Interface to LLM models
"""
import json
import time
import requests
import re
from typing import Dict, List, Any, Optional, Tuple, Union

from src.llm.prompt_builder import PromptBuilder
import config

class LLMService:
    """
    Service for interacting with LLM models.
    """
    
    def __init__(self, analysis_model: str, chat_model: str):
        """
        Initialize the LLM service.
        
        Args:
            analysis_model: Model to use for code analysis
            chat_model: Model to use for chat interface
        """
        self.analysis_model = analysis_model
        self.chat_model = chat_model
        self.prompt_builder = PromptBuilder()
        
        # Statistics
        self.total_tokens_used = 0
        self.total_requests = 0
        self.total_time = 0
    
    def analyze_code(
        self,
        code: str,
        language: str,
        file_path: str,
        analysis_type: str = "standard"
    ) -> Tuple[str, int]:
        """
        Analyze code for issues.
        
        Args:
            code: Code to analyze
            language: Programming language
            file_path: Path to the file
            analysis_type: Type of analysis to perform
            
        Returns:
            Tuple of (analysis result, tokens used)
        """
        # Build prompt
        prompt = self.prompt_builder.build_analysis_prompt(
            code=code,
            language=language,
            file_path=file_path,
            analysis_type=analysis_type
        )
        
        # Set temperature based on analysis type
        temperature = 0.7  # Higher temperature for more critical analysis
        if analysis_type == "security":
            temperature = 0.8  # Even higher for security to find more potential issues
        
        # Call LLM
        response, tokens_used = self._call_ollama(
            model=self.analysis_model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=config.MAX_TOKENS
        )
        
        return response, tokens_used
    
    def generate_fixes(
        self,
        code: str,
        language: str,
        file_path: str,
        issues: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Generate fixes for issues in code.
        
        Args:
            code: Code to fix
            language: Programming language
            file_path: Path to the file
            issues: List of issues to fix
            context: Additional context for fixing
            
        Returns:
            Tuple of (fixed code, tokens used)
        """
        # Build prompt
        prompt = self.prompt_builder.build_fix_prompt(
            code=code,
            language=language,
            file_path=file_path,
            issues=issues,
            context=context
        )
        
        # Call LLM with lower temperature for more conservative fixes
        response, tokens_used = self._call_ollama(
            model=self.analysis_model,
            prompt=prompt,
            temperature=0.2,
            max_tokens=config.MAX_TOKENS
        )
        
        # Extract code block from response
        fixed_code = self._extract_code_block(response, language)
        
        # If no code block found, use the entire response
        if not fixed_code:
            fixed_code = response
        
        return fixed_code, tokens_used
    
    def generate_project_analysis(
        self,
        project_name: str,
        project_structure: Dict[str, Any],
        file_count: int,
        issue_count: int,
        top_issues: List[Tuple[str, int]],
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> Tuple[str, int]:
        """
        Generate project-level analysis.
        
        Args:
            project_name: Name of the project
            project_structure: Structure of the project
            file_count: Number of files analyzed
            issue_count: Number of issues found
            top_issues: Top issues found
            file_analyses: Analyses of individual files
            
        Returns:
            Tuple of (project analysis, tokens used)
        """
        # Build prompt
        prompt = self.prompt_builder.build_project_analysis_prompt(
            project_name=project_name,
            project_structure=project_structure,
            file_count=file_count,
            issue_count=issue_count,
            top_issues=top_issues,
            file_analyses=file_analyses
        )
        
        # Call LLM
        response, tokens_used = self._call_ollama(
            model=self.analysis_model,
            prompt=prompt,
            temperature=0.5,
            max_tokens=config.MAX_TOKENS
        )
        
        return response, tokens_used
    
    def generate_growth_recommendations(
        self,
        project_name: str,
        project_structure: Dict[str, Any],
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> Tuple[str, int]:
        """
        Generate growth recommendations for the project.
        
        Args:
            project_name: Name of the project
            project_structure: Structure of the project
            file_analyses: Analyses of individual files
            
        Returns:
            Tuple of (growth recommendations, tokens used)
        """
        # Build prompt
        prompt = self.prompt_builder.build_growth_recommendations_prompt(
            project_name=project_name,
            project_structure=project_structure,
            file_analyses=file_analyses
        )
        
        # Call LLM
        response, tokens_used = self._call_ollama(
            model=self.analysis_model,
            prompt=prompt,
            temperature=0.6,
            max_tokens=config.MAX_TOKENS
        )
        
        return response, tokens_used
    
    def generate_security_overview(
        self,
        project_name: str,
        security_issues: List[Dict[str, Any]],
        file_analyses: Dict[str, Dict[str, Any]]
    ) -> Tuple[str, int]:
        """
        Generate a security overview for the project.
        
        Args:
            project_name: Name of the project
            security_issues: Security issues found
            file_analyses: Analyses of individual files
            
        Returns:
            Tuple of (security overview, tokens used)
        """
        # Build prompt
        prompt = self.prompt_builder.build_security_overview_prompt(
            project_name=project_name,
            security_issues=security_issues,
            file_analyses=file_analyses
        )
        
        # Call LLM
        response, tokens_used = self._call_ollama(
            model=self.analysis_model,
            prompt=prompt,
            temperature=0.5,
            max_tokens=config.MAX_TOKENS
        )
        
        return response, tokens_used
    
    def chat(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Chat with the LLM.
        
        Args:
            message: User message
            conversation_history: Previous conversation history
            context: Additional context for the conversation
            
        Returns:
            Tuple of (response, tokens used)
        """
        # Build prompt
        prompt = self.prompt_builder.build_chat_prompt(
            message=message,
            conversation_history=conversation_history,
            context=context
        )
        
        # Call LLM
        response, tokens_used = self._call_ollama(
            model=self.chat_model,
            prompt=prompt,
            temperature=0.7,
            max_tokens=config.MAX_TOKENS
        )
        
        return response, tokens_used
    
    def _call_ollama(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Tuple[str, int]:
        """
        Call Ollama API.
        
        Args:
            model: Model to use
            prompt: Prompt to send
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (response, tokens used)
        """
        start_time = time.time()
        
        # Prepare API URL
        api_url = f"{config.OLLAMA_BASE_URL}/api/{config.OLLAMA_API_VERSION}/generate"
        
        # Prepare request data
        data = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "raw": True,
        }
        
        try:
            # Make API call
            response = requests.post(api_url, json=data, timeout=config.TIMEOUT_SECONDS)
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Extract response text
            generated_text = response_data.get("response", "")
            
            # Get token usage
            tokens_used = response_data.get("eval_count", 0) + response_data.get("prompt_eval_count", 0)
            
            # Update statistics
            self.total_tokens_used += tokens_used
            self.total_requests += 1
            self.total_time += time.time() - start_time
            
            return generated_text, tokens_used
            
        except requests.exceptions.Timeout:
            print(f"Error: Request to Ollama API timed out after {config.TIMEOUT_SECONDS} seconds")
            return "Request timed out. Please try again later.", 0
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return f"Error calling LLM API: {e}", 0
    
    def _extract_code_block(self, text: str, language: str) -> Optional[str]:
        """
        Extract code block from text.
        
        Args:
            text: Text containing code block
            language: Programming language
            
        Returns:
            Code block if found, None otherwise
        """
        # Pattern for code blocks in markdown
        pattern = r"```(?:" + language + r")?\s*([\s\S]*?)\s*```"
        
        # Find all code blocks
        matches = re.findall(pattern, text, re.MULTILINE)
        
        # Return the first code block
        return matches[0] if matches else None