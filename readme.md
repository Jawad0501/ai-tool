# AI-Powered Project Analyzer

This is a Python-based AI-powered project analysis tool using DeepSeek-R1. It identifies frameworks, determines relevant files, and analyzes them based on user requests.

## Features
- Identifies frameworks used in a project based on directory structure.
- Determines relevant files for analysis based on user queries.
- Reads and processes selected files for AI-assisted analysis.
- Uses DeepSeek-R1 API for AI-powered insights.

## Requirements
- Python 3.7+
- `requests` module

## Installation
Clone the repository and install dependencies:
```sh
pip install requests
```

## Usage
Run the script with the following command:
```sh
python script.py analyze <project_path> --prompt "Your analysis request"
```

### Example:
```sh
python script.py analyze . --prompt "Identify security vulnerabilities." # '.' is necessary for determining the root directory
```

## API Configuration
The tool communicates with DeepSeek-R1 API via:
```
DEEPSEEK_API_URL = "http://127.0.0.1:11434/api/generate"
```
Ensure the API is running before execution.

## Limitations
- The AI response must strictly follow JSON format.
- API availability is required for analysis.

