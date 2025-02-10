#!/bin/bash

# Define the path to your Python script
SCRIPT_PATH="/Users/authlab/Desktop/ai-tool/ai_tool.py"

# Call the Python script with the "analyze" action and pass the prompt argument
python3 "$SCRIPT_PATH" analyze . --prompt "$1"