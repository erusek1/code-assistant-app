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

1. Clone this repository
2. Install dependencies with `pip install -r requirements.txt`
3. Ensure Ollama is running with the required models

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

## Project Structure

```
├── config.py                  # Configuration settings
├── main.py                    # Main entry point
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

### Coming Soon

- Interactive chat interface for code discussions
- Project creation wizard
- Integration with static analysis tools
- Diff-based analysis and fixes

## License

This project is licensed under the MIT License.
