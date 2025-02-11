# AI-Powered Project Analyzer

This is a Python-based AI-powered project analysis tool using Qwen2.5-Coder. It identifies frameworks, determines relevant files, and analyzes them based on user requests.

## Features
- Identifies frameworks used in a project based on directory structure.
- Determines relevant files for analysis based on user queries.
- Reads and processes selected files for AI-assisted analysis.
- Uses Qwen2.5-Coder API for AI-powered insights.

## Requirements
- Python 3.7+
- `requests` module
- Ollama 

## Installation
Clone the repository and install dependencies:
```sh
pip install requests
```

## Usage
Run the script with the following command:
```sh
/path/to/dist/main analyze <project_path> --prompt "Your analysis request"
```


## Adding Terminal Alias

To simplify access to the tool, you can create a terminal alias:

1. Open your shell configuration file (`~/.bashrc` for Bash, `~/.zshrc` for Zsh, or `~/.bash_profile` for macOS Bash).
2. Add the following line:
   ```sh
   alias aianalyze='/path/to/dist/main analyze . --prompt'  # '.' is used to specify the current directory
   ```
3. Save the file and apply the changes:
   ```sh
   source ~/.bashrc   # or source ~/.zshrc
   ```
4. Now, you can run the tool using:
   ```sh
   aianalyze "Your analysis request"
   ```


### Example:
```sh
/path/to/dist/main . --prompt "Identify security vulnerabilities." # '.' is necessary for determining the root directory
```

Or if you have created alias

```sh
aianalyze "Identify security vulnerabilities." 
```

## API Configuration
The tool communicates with DeepSeek-R1 API via:
```
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
```
Ensure the API is running before execution.

## Limitations
- The AI response must strictly follow JSON format.
- API availability is required for analysis.


