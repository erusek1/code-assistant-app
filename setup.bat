@echo off
echo === Code Assistant App Setup ===
echo This script will install required dependencies and verify your environment.

:: Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found! Please install Python 3.8 or higher.
    echo Visit https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if pip is installed
pip --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip not found! Please ensure pip is installed with Python.
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

:: Activate virtual environment
echo Activating virtual environment...
call .\venv\Scripts\activate

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo Installing dependencies...
pip install -r requirements.txt

:: Verify Ollama installation
echo Checking for Ollama...
curl -s http://localhost:11434/api/tags > nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Ollama API not accessible at http://localhost:11434
    echo Please ensure Ollama is installed and running.
    echo Visit https://ollama.com/download for installation instructions.
) else (
    echo Ollama is running.
)

:: Check for required models
echo Checking for required LLM models...
curl -s http://localhost:11434/api/tags > .model_check.json
findstr /C:"codellama" .model_check.json > nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: CodeLlama model not found in Ollama.
    echo Please run: ollama pull codellama:34b
)

findstr /C:"deepseek-coder" .model_check.json > nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: DeepSeek Coder model not found in Ollama.
    echo Please run: ollama pull deepseek-coder:33b
)

:: Clean up
del .model_check.json > nul 2>&1

echo.
echo Setup complete!
echo To use the code assistant, run: python main.py analyze PATH_TO_YOUR_CODE
echo.
pause