# Code Assistant

A comprehensive tool for analyzing, fixing, and creating code projects locally using LLM models through Ollama.

## Features

- **Code Analysis**: Thoroughly analyze code files and directories to identify issues, security flaws, performance bottlenecks, and growth opportunities
- **Issue Resolution**: Automatically fix identified issues with accurate, context-aware solutions
- **Growth Planning**: Receive enterprise-level recommendations for scaling your codebase
- **Memory System**: Stores analyses to understand entire programs and track changes over time
- **Multi-Model Support**: Uses specialized LLMs for different tasks (CodeLlama for analysis, DeepSeek for chat)

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- Required LLM models:
  - `codellama:34b` for code analysis and fixes
  - `deepseek-coder:33b` for chat interface

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/code-assistant.git
   cd code-assistant
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Ensure Ollama is running with the required models:
   ```bash
   ollama pull codellama:34b
   ollama pull deepseek-coder:33b
   ```

## Usage

### Analyzing Code

To analyze a directory of code:

```bash
python main.py analyze /path/to/your/project
```

This will create a detailed analysis report highlighting issues, security concerns, and growth opportunities.

Options:
- `--fresh`: Perform a fresh analysis without using previous context
- `--output`: Specify path to save the analysis report (default: analysis_report.md)

### Fixing Issues

After running an analysis, you can fix the identified issues:

```bash
python main.py fix /path/to/your/project
```

This will generate fixed versions of your files based on the issues found in the analysis.

Options:
- `--analysis`: Path to the analysis file to use (default: analysis_report.md)
- `--output-dir`: Directory to save fixed files (default: fixed_files)

### Listing Analyses

To see all previous analyses:

```bash
python main.py list
```

## Architecture

The code assistant is built with a modular architecture:

- **Analyzer**: Responsible for analyzing code and identifying issues
- **Fixer**: Implements fixes based on analysis results
- **Memory**: Stores analysis results and project context for better understanding
- **LLM Service**: Interface to LLM models through Ollama
- **Utils**: File operations, reporting, and other utilities

## Configuration

You can customize the behavior of the code assistant by editing the `config.py` file:

- Change LLM models
- Adjust analysis settings
- Modify file extensions to analyze
- Set exclude patterns for files/directories to skip
- Configure timeout and token limits
- Specify minimum issues to find

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.