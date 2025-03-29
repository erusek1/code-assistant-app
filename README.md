# Code Assistant App

A comprehensive tool for analyzing, fixing, and creating code projects locally using LLM models through Ollama.

## Features

- **Code Analysis**: Scan entire project directories for coding issues, bugs, and improvements
- **Code Fixing**: Automatically fix identified issues with LLM-powered solutions
- **Project Creation**: Create new projects from scratch based on detailed requirements
- **Chat Interface**: Discuss issues, improvements, or new features with an AI assistant
- **Local Operation**: All processing happens locally on your machine via Ollama

## Getting Started

### Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running on your machine
- CodeLlama 34b model for code analysis (`ollama pull codellama:34b`)
- DeepSeek Coder 33b model for chat interface (`ollama pull deepseek-coder:33b`)

### Installation

#### Easy Setup

1. Clone this repository
2. Run the setup script:
   - Windows: Double-click `setup.bat` or run it from Command Prompt
   - Linux/Mac: Run `chmod +x setup.sh && ./setup.sh` from Terminal

#### Manual Setup

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Ensure Ollama is running with the required models

### Usage

#### Analyzing Code

```bash
python main.py analyze /path/to/project
```

The analysis will scan all code files in the project, identify issues, and generate a comprehensive report.

#### Fixing Issues

```bash
python main.py fix /path/to/project --analysis analysis_report.md
```

This will fix issues identified in the analysis report and save the fixed files to a directory.

#### Listing Past Analyses

```bash
python main.py list
```

View a list of all past analyses stored in the system.

## Troubleshooting

### JSON Parsing Errors

If you encounter JSON parsing errors, the tool will attempt to analyze the files anyway. The improved error handling will:

1. Try to read JSON files with multiple encoding strategies
2. Fall back to binary reading for problematic files
3. Continue with analysis even when some files can't be fully parsed

### Ollama Connection Issues

If you're seeing Ollama connection errors:

1. Ensure Ollama is installed and running (`ollama serve`)
2. Verify the models are installed (`ollama list`)
3. Check that the Ollama API is accessible at http://localhost:11434
4. The tool will automatically retry API calls with exponential backoff

### Large Files or Complex Projects

For very large projects:

1. Consider analyzing specific directories rather than the entire project
2. Use the `--fresh` flag to force fresh analysis: `python main.py analyze /path/to/project --fresh`
3. Increase the `TIMEOUT_SECONDS` value in `config.py` if needed

## How It Works

1. The code analyzer scans your project files, identifying potential issues using the CodeLlama model.
2. It generates a detailed report with issues categorized by file, with line numbers and descriptions.
3. The code fixer can then apply intelligent fixes to these issues, creating corrected versions of your files.
4. All analyses are stored locally for future reference and comparison.

## Configuration

Key settings can be adjusted in `config.py`:

- `ANALYSIS_MODEL`: Model to use for code analysis
- `CHAT_MODEL`: Model to use for chat interface
- `ANALYSIS_TEMPERATURE`: Temperature setting for analysis (higher = more creative/critical)
- `FIX_TEMPERATURE`: Temperature setting for fixes (lower = more conservative fixes)
- `CODE_EXTENSIONS`: File extensions to analyze
- `TIMEOUT_SECONDS`: Maximum time to wait for LLM responses

## Project Structure

```
├── config.py                  # Configuration settings
├── main.py                    # Main entry point
├── requirements.txt           # Required Python packages
├── setup.bat                  # Windows setup script
├── setup.sh                   # Linux/Mac setup script
├── src/
│   ├── analyzer/             # Code analysis components
│   ├── fixer/                # Code fixing components
│   ├── llm/                  # LLM interaction components
│   ├── memory/               # Session memory components
│   └── utils/                # Utility functions
└── data/                      # Data storage directory
```

## Improvements and Features

### Recently Added

- Specialized analysis types (security, performance, growth)
- Issue counting and tracking
- Enhanced critical analysis with higher temperature
- Detailed project-level summaries with issue counts
- Improved JSON & file handling
- Enhanced error handling and recovery
- Automatic retries for LLM API calls

### Coming Soon

- Interactive chat interface for code discussions
- Project creation wizard
- Integration with static analysis tools
- Diff-based analysis and fixes

## License

This project is licensed under the MIT License.