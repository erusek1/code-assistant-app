"""
Configuration settings for the Code Assistant
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True, parents=True)

# LLM models
ANALYSIS_MODEL = "codellama:34b"  # Use CodeLlama for analysis and fixes
CHAT_MODEL = "deepseek-coder:33b"  # Use DeepSeek for chat interface

# Analysis settings
MAX_TOKENS = 4096
ANALYSIS_TEMPERATURE = 0.7  # Higher temperature for more critical analysis
FIX_TEMPERATURE = 0.2  # Lower temperature for more conservative fixes
TIMEOUT_SECONDS = 120  # 2 minutes timeout for LLM calls

# File extensions to analyze
CODE_EXTENSIONS = {
    # Python
    ".py": "python",
    # JavaScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    # Web
    ".html": "html",
    ".css": "css",
    # Java
    ".java": "java",
    # C-family
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    # C#
    ".cs": "csharp",
    # Go
    ".go": "go",
    # Ruby
    ".rb": "ruby",
    # PHP
    ".php": "php",
    # Swift
    ".swift": "swift",
    # Rust
    ".rs": "rust",
    # Kotlin
    ".kt": "kotlin",
    # Shell scripts
    ".sh": "bash",
    ".bash": "bash",
    # Config files
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    # Documentation
    ".md": "markdown",
}

# Files to exclude from analysis
EXCLUDE_PATTERNS = [
    "**/node_modules/**",
    "**/.git/**",
    "**/venv/**",
    "**/__pycache__/**",
    "**/.DS_Store",
    "**/dist/**",
    "**/build/**",
    "**/*.min.js",
    "**/*.min.css",
]

# Analysis store path
ANALYSIS_STORE_PATH = DATA_DIR / "analysis_store.json"

# Project context path
PROJECT_CONTEXT_PATH = DATA_DIR / "project_context.json"

# Number of issues to find (minimum)
MIN_ISSUES_TO_FIND = 2  # Force LLM to find at least this many issues

# Analysis types
ANALYSIS_TYPES = [
    "standard",   # General code quality and best practices
    "security",   # Security vulnerabilities
    "performance", # Performance bottlenecks
    "growth",     # Scalability and architectural improvements
    "thorough",   # Combination of all types
]

# External API configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_VERSION = ""