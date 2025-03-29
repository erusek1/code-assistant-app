#!/usr/bin/env python3
"""
Enhanced LLM Service - Provides improved interactions with LLM models
"""
import os
import json
import time
import re
import httpx
from typing import Dict, List, Tuple, Optional, Any, Union
import requests
from requests.exceptions import RequestException
import logging
import concurrent.futures

from src.llm.prompt_builder import PromptBuilder
import config

class EnhancedLLMService:
    """
    An enhanced service for interacting with multiple LLM models.
    """
    
    def __init__(
        self,
        analysis_model: str = config.ANALYSIS_MODEL,
        chat_model: str = config.CHAT_MODEL,
        base_url: str = config.OLLAMA_BASE_URL,
        timeout: int = config.TIMEOUT_SECONDS
    ):
        self.analysis_model = analysis_model
        self.chat_model = chat_model
        self.base_url = base_url
        self.timeout = timeout
        self.prompt_builder = PromptBuilder()
        
        # Statistics
        self.total_tokens = 0
        self.total_requests = 0
        self.request_times = []
        self.errors = []
        
        # In-memory conversation history
        self.conversation_history = []
    
    def analyze_code(
        self,
        code: str,
        language: str,
        file_path: str,
        analysis_type: str = "standard",
        min_issues: int = config.MIN_ISSUES_TO_FIND,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """
        Analyze code using the analysis model.
        
        Args:
            code: The code to analyze
            language: The programming language
            file_path: Path to the file being analyzed
            analysis_type: Type of analysis (standard, security, performance, thorough)
            min_issues: Minimum number of issues to find
            context: Optional context from previous analyses
            
        Returns:
            Tuple of (analysis result, tokens used)
        """
        # Create system prompt
        system_prompt = self.prompt_builder.build_analysis_prompt(
            language=language,
            file_path=file_path,
            analysis_type=analysis_type,
            min_issues=min_issues
        )
        
        # Include context if available
        user_prompt = code
        if context:
            # Extract relevant parts of the context to include
            context_summary = context.get("summary", "")
            if context_summary:
                user_prompt = f"Previous analysis summary:\n{context_summary}\n\n{user_prompt}"
        
        # Set temperature based on analysis type
        temp = 0.2  # Default conservative
        if analysis_type == "thorough":
            temp = 0.7  # More creative for thorough analysis
        elif analysis_type == "security":
            temp = 0.5  # Balanced for security analysis
        
        # Call LLM with the analysis model
        response, tokens = self._call_llm(
            model=self.analysis_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temp,
            max_tokens=config.MAX_TOKENS
        )
        
        # Try to extract structured JSON, with fallback to raw response
        structured_response = self._extract_json(response)
        if structured_response and config.ALLOW_PARTIAL_JSON:
            # Valid JSON found, return it
            return json.dumps(structured_response, indent=2), tokens
        
        # Fall back to raw response
        return response, tokens
    
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
            code: The original code
            language: The programming language
            file_path: Path to the file being fixed
            issues: List of issues to fix
            context: Optional context from previous analyses
            
        Returns:
            Tuple of (fixed code, tokens used)
        """
        # Create system prompt for fixing code
        system_prompt = self.prompt_builder.build_fix_prompt(
            language=language,
            file_path=file_path
        )
        
        # Format issues into a structured prompt
        issues_text = "\n".join([
            f"Issue #{i+1}: {issue.get('description', 'No description')} " + 
            (f"(Line {issue.get('line_number', 'unknown')})" if issue.get('line_number') else "")
            for i, issue in enumerate(issues)
        ])
        
        # Combine all prompts
        user_prompt = f"File: {file_path}\n\nIssues to fix:\n{issues_text}\n\nOriginal code:\n```{language}\n{code}\n```"
        
        if context:
            user_prompt = f"Context:\n{context}\n\n{user_prompt}"
        
        # Call LLM with the analysis model and conservative temperature
        response, tokens = self._call_llm(
            model=self.analysis_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=config.FIX_TEMPERATURE,
            max_tokens=config.MAX_TOKENS
        )
        
        # Extract code from the response
        fixed_code = self._extract_code(response)
        
        # Fall back to original if extraction failed
        if not fixed_code:
            fixed_code = code
        
        return fixed_code, tokens
    
    def chat_about_code(
        self,
        messages: List[Dict[str, str]],
        project_path: Optional[str] = None,
        related_files: Optional[List[str]] = None,
        code_snippets: Optional[List[str]] = None,
        remember_context: bool = True
    ) -> Tuple[str, int]:
        """
        Chat with the LLM about code.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            project_path: Optional path to the current project
            related_files: Optional list of related file paths
            code_snippets: Optional list of code snippets
            remember_context: Whether to remember this exchange in history
            
        Returns:
            Tuple of (response text, tokens used)
        """
        # Create system prompt for code chat
        system_prompt = self.prompt_builder.build_chat_prompt(
            project_path=project_path,
            related_files=related_files
        )
        
        # Prepare context from code snippets
        context = ""
        if code_snippets:
            context = "Relevant code snippets:\n\n" + "\n\n".join(code_snippets)
            # Add context as an assistant message
            if context:
                messages.insert(0, {"role": "assistant", "content": context})
        
        # Format messages for Ollama
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Call the chat model
        response, tokens = self._call_llm_chat(
            model=self.chat_model,
            messages=formatted_messages,
            system_prompt=system_prompt,
            temperature=0.7,  # More creative for chat
            max_tokens=config.MAX_TOKENS
        )
        
        # Update conversation history if needed
        if remember_context:
            if len(formatted_messages) > 0:
                self.conversation_history.extend(formatted_messages)
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Trim history if it gets too long
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
        
        return response, tokens
    
    def generate_code(
        self,
        description: str,
        language: str,
        file_path: Optional[str] = None,
        existing_code: Optional[str] = None,
        related_files: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, int]:
        """
        Generate code based on a description.
        
        Args:
            description: Description of the code to generate
            language: The programming language
            file_path: Optional path for the file to create
            existing_code: Optional existing code to modify
            related_files: Optional list of related files (path and content)
            
        Returns:
            Tuple of (generated code, tokens used)
        """
        # Create system prompt for code generation
        system_prompt = self.prompt_builder.build_generation_prompt(
            language=language,
            file_path=file_path
        )
        
        # Prepare user prompt
        user_prompt = f"Generate code in {language} based on the following description:\n\n{description}"
        
        if existing_code:
            user_prompt += f"\n\nExisting code to modify or extend:\n```{language}\n{existing_code}\n```"
        
        # Add related files context
        if related_files:
            related_context = "Related files for context:\n\n"
            for file_info in related_files:
                file_path = file_info.get("path", "unknown")
                content = file_info.get("content", "")
                if content:
                    lang = self._guess_language_from_path(file_path)
                    related_context += f"File: {file_path}\n```{lang}\n{content}\n```\n\n"
            user_prompt += f"\n\n{related_context}"
        
        # Call LLM with the analysis model
        response, tokens = self._call_llm(
            model=self.analysis_model,  # Use analysis model for code generation
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,  # Balanced temperature for generation
            max_tokens=config.MAX_TOKENS
        )
        
        # Extract code from the response
        generated_code = self._extract_code(response)
        
        # If no code was extracted, use the full response
        if not generated_code:
            generated_code = response
        
        return generated_code, tokens
    
    def create_project_structure(
        self,
        description: str,
        project_name: str,
        technologies: List[str],
        directory_structure: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Generate a project structure based on a description.
        
        Args:
            description: Description of the project
            project_name: Name of the project
            technologies: List of technologies to use
            directory_structure: Optional existing directory structure
            
        Returns:
            Tuple of (project structure, tokens used)
        """
        # Create system prompt for project structure generation
        system_prompt = self.prompt_builder.build_project_prompt()
        
        # Prepare user prompt
        user_prompt = f"Create a project structure for '{project_name}' with the following description:\n\n{description}\n\nTechnologies: {', '.join(technologies)}"
        
        if directory_structure:
            user_prompt += f"\n\nExisting directory structure:\n```json\n{json.dumps(directory_structure, indent=2)}\n```"
        
        # Call LLM with the chat model
        response, tokens = self._call_llm(
            model=self.chat_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=config.MAX_TOKENS
        )
        
        # Try to extract a JSON structure
        project_structure = self._extract_json(response)
        
        # If extraction failed, create a minimal structure
        if not project_structure:
            project_structure = {
                "project_name": project_name,
                "description": description,
                "technologies": technologies,
                "files": [],
                "directories": []
            }
        
        return project_structure, tokens
    
    def _call_llm(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Tuple[str, int]:
        """
        Call the LLM with a system prompt and user prompt.
        
        Args:
            model: Model to use
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (response text, tokens used)
        """
        start_time = time.time()
        self.total_requests += 1
        
        # Prepare API request
        url = f"{self.base_url}/api/generate"
        data = {
            "model": model,
            "prompt": user_prompt,
            "system": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        tokens = 0
        retries = 0
        max_retries = config.MAX_RETRIES
        retry_delay = config.INITIAL_RETRY_DELAY
        
        while retries <= max_retries:
            try:
                response = requests.post(url, json=data, timeout=self.timeout)
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get("response", "")
                tokens = result.get("total_tokens", 0) or tokens
                
                self.total_tokens += tokens
                
                # Record request time
                request_time = time.time() - start_time
                self.request_times.append(request_time)
                
                return response_text, tokens
                
            except RequestException as e:
                retries += 1
                if retries > max_retries:
                    error_msg = f"Error calling LLM API after {max_retries} retries: {str(e)}"
                    self.errors.append(error_msg)
                    print(error_msg)
                    return f"Error: {str(e)}", 0
                
                # Exponential backoff
                sleep_time = retry_delay * (2 ** (retries - 1))
                print(f"API call failed, retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
    def _call_llm_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Tuple[str, int]:
        """
        Call the LLM using the chat endpoint.
        
        Args:
            model: Model to use
            messages: List of message dictionaries
            system_prompt: Optional system prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (response text, tokens used)
        """
        start_time = time.time()
        self.total_requests += 1
        
        # Prepare the chat request
        url = f"{self.base_url}/api/chat"
        
        # Prepare data payload
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add system if provided
        if system_prompt:
            data["system"] = system_prompt
        
        tokens = 0
        retries = 0
        max_retries = config.MAX_RETRIES
        retry_delay = config.INITIAL_RETRY_DELAY
        
        while retries <= max_retries:
            try:
                response = requests.post(url, json=data, timeout=self.timeout)
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get("message", {}).get("content", "")
                tokens = result.get("total_tokens", 0) or tokens
                
                self.total_tokens += tokens
                
                # Record request time
                request_time = time.time() - start_time
                self.request_times.append(request_time)
                
                return response_text, tokens
                
            except RequestException as e:
                retries += 1
                if retries > max_retries:
                    error_msg = f"Error calling LLM chat API after {max_retries} retries: {str(e)}"
                    self.errors.append(error_msg)
                    print(error_msg)
                    return f"Error: {str(e)}", 0
                
                # Exponential backoff
                sleep_time = retry_delay * (2 ** (retries - 1))
                print(f"API call failed, retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
    def _extract_code(self, text: str) -> str:
        """
        Extract code blocks from text.
        
        Args:
            text: Text containing code blocks
            
        Returns:
            Extracted code or empty string
        """
        # Look for code blocks with triple backticks
        code_block_pattern = r"```(?:\w+)?\n([\s\S]+?)\n```"
        matches = re.findall(code_block_pattern, text)
        
        if matches:
            return "\n\n".join(matches)
        
        # Fall back to looking for indented blocks if no code blocks found
        lines = text.split("\n")
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            
            if in_code_block:
                code_lines.append(line)
        
        if code_lines:
            return "\n".join(code_lines)
        
        # If no code blocks found, return empty string
        return ""
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text.
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON as dictionary or None
        """
        # Look for JSON inside code blocks
        json_block_pattern = r"```(?:json)?\n([\s\S]+?)\n```"
        matches = re.findall(json_block_pattern, text)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Try to find JSON without code blocks
        json_pattern = r"(\{[\s\S]+\})"
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _guess_language_from_path(self, file_path: str) -> str:
        """
        Guess the programming language from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language identifier
        """
        extension = os.path.splitext(file_path)[1].lower()
        
        return config.CODE_EXTENSIONS.get(extension, "")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about LLM usage.
        
        Returns:
            Dictionary with statistics
        """
        avg_request_time = 0
        if self.request_times:
            avg_request_time = sum(self.request_times) / len(self.request_times)
        
        return {
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "average_request_time": avg_request_time,
            "errors": len(self.errors),
            "tokens_per_request": self.total_tokens / max(1, self.total_requests)
        }
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
