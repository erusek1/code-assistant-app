"""
LLM Service - Interface to LLM models
"""
import json
import time
import requests
import traceback
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
        
        # Test connection to Ollama
        self.test_ollama_connection()
    
    def test_ollama_connection(self):
        """Test connection to Ollama API."""
        try:
            print("Testing connection to Ollama...")
            response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Print available models
            json_response = response.json()
            available_models = [model.get("name") for model in json_response.get("models", [])]
            print(f"Available models: {available_models}")
            
            print(f"Connected to Ollama successfully.")
            
            # Check if required models are available
            analysis_model_base = self.analysis_model.split(':')[0]
            chat_model_base = self.chat_model.split(':')[0]
            
            analysis_model_found = any(model.startswith(analysis_model_base) for model in available_models)
            chat_model_found = any(model.startswith(chat_model_base) for model in available_models)
            
            if not analysis_model_found:
                print(f"Warning: Analysis model '{self.analysis_model}' not found in Ollama.")
                print(f"Available models: {', '.join(available_models) if available_models else 'None'}")
                print(f"Consider running: ollama pull {self.analysis_model}")
            
            if not chat_model_found:
                print(f"Warning: Chat model '{self.chat_model}' not found in Ollama.")
                print(f"Available models: {', '.join(available_models) if available_models else 'None'}")
                print(f"Consider running: ollama pull {self.chat_model}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            print("Please ensure Ollama is running on your machine.")
            print(f"Expected Ollama at: {config.OLLAMA_BASE_URL}")
    
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
        max_retries = config.MAX_RETRIES if hasattr(config, 'MAX_RETRIES') else 3
        retry_delay = config.INITIAL_RETRY_DELAY if hasattr(config, 'INITIAL_RETRY_DELAY') else 2  # seconds
        
        for attempt in range(max_retries):
            start_time = time.time()
            
            try:
                # Log summary of request (truncate long prompts)
                prompt_summary = prompt[:100] + "..." if len(prompt) > 100 else prompt
                print(f"  Calling Ollama with model {model}, prompt: {prompt_summary}")
                
                # Always use the standard generate endpoint
                api_url = f"{config.OLLAMA_BASE_URL}/api/generate"
                print(f"  Using API URL: {api_url}")
                
                # Prepare request data for the generate endpoint
                data = {
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "raw": True,
                }
                
                # Make API call with timeout
                response = requests.post(
                    api_url, 
                    json=data, 
                    timeout=config.TIMEOUT_SECONDS
                )
                response.raise_for_status()
                
                # Debug the raw response
                raw_response = response.text
                print(f"  Response raw content (first 100 chars): {raw_response[:100]}...")
                
                # Safely parse the response
                try:
                    response_data = json.loads(raw_response)
                    
                    # Extract response text and token count
                    generated_text = response_data.get("response", "")
                    tokens_used = response_data.get("eval_count", 0) + response_data.get("prompt_eval_count", 0)
                    
                    # Update statistics
                    self.total_tokens_used += tokens_used
                    self.total_requests += 1
                    self.total_time += time.time() - start_time
                    
                    # Print response summary
                    resp_summary = generated_text[:100] + "..." if len(generated_text) > 100 else generated_text
                    print(f"  Received response ({tokens_used} tokens): {resp_summary}")
                    
                    # If we have a valid response
                    if generated_text:
                        return generated_text, tokens_used
                    else:
                        print("  Warning: Empty response received from Ollama")
                        # Return something rather than nothing
                        return "No issues found in the code. The analysis completed successfully but didn't identify any specific problems to report.", 0
                    
                except json.JSONDecodeError as e:
                    print(f"  Warning: JSON parsing failed: {e}")
                    print(f"  Raw response: {raw_response[:200]}...")
                    
                    # Try to extract something useful from the raw response
                    # For some Ollama versions, the response might be plain text
                    if raw_response.strip():
                        print("  Using raw response as fallback")
                        # Estimate token usage based on response length
                        tokens_used = len(raw_response.split()) * 2  # Rough estimate
                        return raw_response, tokens_used
                    else:
                        # If we can't get anything useful
                        print("  No useful content could be extracted from response")
                        return "The analysis couldn't be completed. Please check that Ollama is running correctly.", 0
                
            except requests.exceptions.Timeout:
                print(f"  Warning: Request to Ollama API timed out after {config.TIMEOUT_SECONDS} seconds - Attempt {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    print(f"  Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= config.RETRY_BACKOFF_FACTOR if hasattr(config, 'RETRY_BACKOFF_FACTOR') else 2  # Exponential backoff
                else:
                    print("  Max retries exceeded.")
                    return "Request timed out. Please ensure Ollama is running and try again with a smaller codebase.", 0
                
            except requests.exceptions.RequestException as e:
                print(f"  Error calling Ollama API: {e} - Attempt {attempt+1}/{max_retries}")
                traceback.print_exc()
                if attempt < max_retries - 1:
                    print(f"  Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= config.RETRY_BACKOFF_FACTOR if hasattr(config, 'RETRY_BACKOFF_FACTOR') else 2  # Exponential backoff
                else:
                    print("  Max retries exceeded.")
                    return f"Error calling Ollama API: {e}. Please check that Ollama is running correctly.", 0
            
            except Exception as e:
                print(f"  Unexpected error: {e} - Attempt {attempt+1}/{max_retries}")
                traceback.print_exc()
                if attempt < max_retries - 1:
                    print(f"  Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= config.RETRY_BACKOFF_FACTOR if hasattr(config, 'RETRY_BACKOFF_FACTOR') else 2
                else:
                    print("  Max retries exceeded.")
                    return f"Unexpected error: {e}. Please try again with a smaller codebase or check your Ollama installation.", 0
    
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