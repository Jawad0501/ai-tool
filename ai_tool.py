import argparse
import requests
import os
import json
import re
import shutil
import subprocess

OLLAMA_INSTALL_URL = "https://ollama.com/download"
OLLAMA_INSTALL_CMD = "curl -fsSL https://ollama.com/install.sh | sh"  # For Linux/macOS
OLLAMA_MODEL_NAME = "codegemma"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_API = "http://localhost:11434"
EXCLUDED_FOLDERS = ["vendor", "node_modules", ".git"]


# OLLAMA INSTALLATION
def is_ollama_installed():
    """Check if Ollama is installed by looking for the executable."""
    return shutil.which("ollama") is not None

def is_model_installed(model_name):
    """Check if a specific model is installed in Ollama."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        return model_name in result.stdout
    except FileNotFoundError:
        return False

def prompt_installation():
    """Prompt the user for installation of Ollama and the model."""
    print("\n🚨 Ollama or the required model is missing! 🚨")
    print("👉 Ollama (AI model runner) is required to run this script.")
    print(f"👉 The '{OLLAMA_MODEL_NAME}' model is also required for analysis.")
    print("\n📦 Estimated Disk Space:")
    print("   - Ollama: ~500MB")
    print("   - codegemma model: ~5GB")
    
    choice = input("\nDo you want to install them now? (y/n): ").strip().lower()
    
    if choice == 'y':
        install_ollama()
        install_model(OLLAMA_MODEL_NAME)
    else:
        print("\n❌ Installation aborted. Exiting...")
        exit()

def install_ollama():
    """Install Ollama based on the user's OS."""
    print("\n🚀 Installing Ollama...")

    if os.name == 'posix':  # macOS/Linux
        subprocess.run(OLLAMA_INSTALL_CMD, shell=True, check=True)
    elif os.name == 'nt':  # Windows
        print(f"\n🔗 Please download and install Ollama manually: {OLLAMA_INSTALL_URL}")
        input("Press Enter after installation to continue...")
    else:
        print("❌ Unsupported OS. Please install Ollama manually.")
        exit()

def install_model(model_name):
    """Install a specific model in Ollama."""
    print(f"\n🚀 Downloading model '{model_name}' (this may take a while)...")
    subprocess.run(["ollama", "pull", model_name], check=True)

def check_ollama_and_setup():
    """Ensure Ollama and the required model are installed before proceeding."""
    if not is_ollama_installed():
        prompt_installation()

    if not is_model_installed(OLLAMA_MODEL_NAME):
        install_model(OLLAMA_MODEL_NAME)

    print("\n✅ All requirements are installed. Starting workflow...")


def check_api_availability():
    try:
        response = requests.get(OLLAMA_API)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def generate_text(prompt):
    try:
        response = requests.post(OLLAMA_API_URL, json={"model": OLLAMA_MODEL_NAME, "prompt": prompt, "stream": False})
        response.raise_for_status()
        return response.json().get("response", "No response received")
    except requests.exceptions.RequestException as e:
        return f"Error during API request: {str(e)}"

# def map_directory_structure(dir_path):
#     structure = {}
#     for root, dirs, files in os.walk(dir_path):
#         dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS]
#         relative_path = os.path.relpath(root, dir_path)
#         structure[relative_path if relative_path != "." else ""] = {"dirs": dirs, "files": files}
#         # print(structure)
#     return structure

def map_directory_structure(dir_path):
    def get_directory_tree(path):
        # List to store subdirectory and file information
        result = {}
        
        # Walk through the directory
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # Exclude directories as specified
                if item not in EXCLUDED_FOLDERS:
                    result[item] = get_directory_tree(item_path)  # Recursively get subdirectory tree
            elif os.path.isfile(item_path):
                result[item] = None  # Files will be stored with a None value (indicating it's a file)

        return result

    # Start building the tree from the root directory
    return {os.path.basename(dir_path): get_directory_tree(dir_path)}

def map_root_directory_structure(dir_path):
    structure = []

    # List the immediate directories and files in the root folder
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path):
            if item not in EXCLUDED_FOLDERS:
                structure.append(item)
        elif os.path.isfile(item_path):
            structure.append(item)

    # Print the structure for debugging (optional)
    # print(structure)
    return structure

def identify_framework(directory_structure):
    prompt = f"""
    Given the following project directory structure:
    {json.dumps(directory_structure, indent=4)}

    Identify the framework(s) used in this project and explain your reasoning. The project may use more than one framework, so return all identified frameworks.

    Return the result strictly in the following JSON format:
    [
    "Framework1",
    "Framework2"
    ]

    Example Responses:
    1. If the project uses Laravel and Vue:
    [
        "Laravel",
        "Vue"
    ]
    2. If the project uses React and Vite:
    [
        "React",
        "Vite"
    ]
    3. If the project only uses WordPress:
    [
        "WordPress"
    ]


    Only return the JSON array and nothing else. I dont need the reasoning.
    """
    response = generate_text(prompt)
    try:
        return {"framework" : json.loads(response)}
    except json.JSONDecodeError:
        return {"framework_detected": False, "framework": "Unknown", "reasoning": response}

# def determine_relevant_files(directory_structure, framework_info, user_request):
#     print(directory_structure);
#     print(user_request);
#     prompt = f"""
#     Given the directory structure:
#     {json.dumps(directory_structure, indent=2)}
#     The project uses {framework_info['framework']}.
#     Based on the user request: "{user_request}", determine which files are most relevant for analysis.
#     Return a list of relevant file paths in JSON {'app/Http/Controllers/StaffController.php', 'composer.json'} format.
#     """
#     response = generate_text(prompt)
#     print(response)

#     try:
#         return json.loads(response)
#     except json.JSONDecodeError:
#         return {"selected_files": [], "reasoning": response}

# def read_selected_files(base_path, selected_files):
#     file_contents = {}
#     for file_path in selected_files:
#         full_path = os.path.join(base_path, file_path)
#         if os.path.exists(full_path):
#             with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
#                 file_contents[file_path] = f.read()
#     return file_contents


def determine_relevant_files(directory_structure, framework_info, user_request):

    # Construct the prompt to pass to the AI
    prompt = f"""
    Given the directory structure:
    {directory_structure}.

    Based on the user request: "{user_request}", determine which files are most relevant for analysis.

    Return a list of relevant file paths strictly following the JSON format:
    ['filePath1', 'filePath2']

    Example Responses:
    1. If the relevant file paths are composer.json and vite.config.js:
    [
        "composer.json",
        "vite.config.js"
    ]



    Only return the JSON array and nothing else. I dont need the reasoning or justification.    
    """
    
    # Call to AI to generate a response
    response = generate_text(prompt)
    print(response)

    file_paths = json.loads(response)

    return {"file_paths" : file_paths}

    # Try to parse the response and return the relevant file paths
    # try:
    #     # Assuming the AI response is a list of file paths as a JSON array of strings
    #     # file_paths = json.loads(response)
    #     # print("File paths:", file_paths)

    #     print(json.loads(response))
        
        
    #     # Ensure the response is an array of strings (file paths)
    #     # if isinstance(file_paths, list) and all(isinstance(item, str) for item in file_paths):
    #     #     return file_paths
    #     # else:
    #     #     return {"selected_files": [], "reasoning": "Invalid format in AI response"}
    # except json.JSONDecodeError:
    #     # If the AI response can't be parsed, return the raw response for debugging
    #     return {"file_paths": [], "reasoning": response}

def read_selected_files(base_path, selected_files):
    file_contents = {}
    for file_path in selected_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                file_contents[file_path] = f.read()
    return file_contents

def analyze_files_with_ai(file_contents, user_request):
    prompt = f"""
    The following files were selected for analysis:
    {json.dumps(file_contents, indent=4)}
    Perform the requested analysis: "{user_request}".
    """
    response = generate_text(prompt)
    return response
    # try:
    #     return json.loads(response)
    # except json.JSONDecodeError:
    #     return {"issues": [], "raw_response": response}

def main():
    parser = argparse.ArgumentParser(description="AI-powered project analysis using DeepSeek-R1.")
    parser.add_argument("action", choices=["analyze"], help="Action to perform")
    parser.add_argument("path", help="Project directory path")
    parser.add_argument("--prompt", required=True, help="User request for analysis")
    args = parser.parse_args()

    if not check_api_availability():
        print("API is unavailable. Exiting.")
        return

    check_ollama_and_setup()

    directory_structure = map_directory_structure(args.path)
    root_directory_structure = map_root_directory_structure(args.path)
    framework_info = identify_framework(directory_structure)
    print(f"Detected Framework: {framework_info['framework']}")
    
    relevant_files = determine_relevant_files(directory_structure, framework_info, args.prompt)
    print(f"Relevant Files: {relevant_files}")

    file_contents = read_selected_files(args.path, relevant_files['file_paths'])
    analysis_results = analyze_files_with_ai(file_contents, args.prompt)
    
    print("\n=== Analysis Results ===\n", json.dumps(analysis_results, indent=2))

if __name__ == "__main__":
    main()
