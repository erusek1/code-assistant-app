#!/bin/bash

echo "=== Code Assistant App Setup ==="
echo "This script will install required dependencies and verify your environment."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python not found! Please install Python 3.8 or higher."
    echo "Visit https://www.python.org/downloads/"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip not found! Please ensure pip is installed with Python."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Verify Ollama installation
echo "Checking for Ollama..."
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "WARNING: Ollama API not accessible at http://localhost:11434"
    echo "Please ensure Ollama is installed and running."
    echo "Visit https://ollama.com/download for installation instructions."
else
    echo "Ollama is running."
fi

# Check for required models
echo "Checking for required LLM models..."
curl -s http://localhost:11434/api/tags > .model_check.json

if ! grep -q "codellama" .model_check.json; then
    echo "WARNING: CodeLlama model not found in Ollama."
    echo "Please run: ollama pull codellama:34b"
fi

if ! grep -q "deepseek-coder" .model_check.json; then
    echo "WARNING: DeepSeek Coder model not found in Ollama."
    echo "Please run: ollama pull deepseek-coder:33b"
fi

# Clean up
rm -f .model_check.json

echo ""
echo "Setup complete!"
echo "To use the code assistant, run: python main.py analyze PATH_TO_YOUR_CODE"
echo ""