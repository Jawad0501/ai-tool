import os
import json
import argparse
import subprocess
import requests
import shutil
import re
import platform
from difflib import get_close_matches  # For fuzzy matching

# Constants
OLLAMA_MODEL_NAME = "qwen2.5-coder"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
EXCLUDED_FOLDERS = ["vendor", "node_modules", ".git"]

# Session Memory with Indexing
class CodeIndex:
    def __init__(self):
        self.index = {}  # { "function_name": "file_path" }
        self.file_snippets = {}  # { "file_path": ["function definitions", ...] }

    def add(self, file_path, function_name, snippet):
        """Add function/class to index"""
        print(f"✅ Indexing {function_name} from {file_path}")  # Debugging
        self.index[function_name.lower()] = file_path
        if file_path not in self.file_snippets:
            self.file_snippets[file_path] = []
        self.file_snippets[file_path].append(snippet)

    def search(self, query):
        """Find relevant files based on query using substring matching"""
        query = query.lower()
        matches = {}

        # Use substring matching for case-insensitive search
        for fn, file_path in self.index.items():
            if query in fn:  # Check if query string is a substring of function name
                matches[fn] = file_path

        return matches

    def search_fuzzy(self, query):
        """Find the closest matches using fuzzy matching"""
        query = query.lower()
        all_functions = list(self.index.keys())
        closest_matches = get_close_matches(query, all_functions, n=3, cutoff=0.6)
        matches = {fn: self.index[fn] for fn in closest_matches}
        return matches

    def get_snippets(self, file_path):
        """Get relevant code snippets"""
        return self.file_snippets.get(file_path, [])

def install_ollama():
    """Install Ollama based on the OS"""
    os_name = platform.system().lower()
    
    if os_name == "darwin":  # macOS
        print("🍏 Installing Ollama on macOS...")
        subprocess.run(["brew", "install", "ollama"], check=True)

    elif os_name == "linux":
        print("🐧 Installing Ollama on Linux...")
        subprocess.run("curl -fsSL https://ollama.com/install.sh | bash", shell=True, check=True)

    elif os_name == "windows":
        print("🖥️ Installing Ollama on Windows...")
        subprocess.run(["powershell", "-Command", "iwr https://ollama.com/install.ps1 -useb | iex"], check=True)

    else:
        print("❌ Unsupported OS. Please install Ollama manually from https://ollama.com")
        exit(1)

    print("✅ Ollama installed successfully!")

# Ollama Check
def check_ollama_and_setup():
    if shutil.which("ollama") is None:
        print("\n❌ Ollama not found. Installing now...")
        install_ollama()
        exit()
    else:
        print("\n✅ Ollama is already installed.")

    subprocess.run(["ollama", "pull", OLLAMA_MODEL_NAME], check=True)
    print("\n✅ Ollama and model are ready.")

# AI Interaction
def generate_text(prompt):
    """Call Ollama AI for text generation"""
    try:
        response = requests.post(OLLAMA_API_URL, json={"model": OLLAMA_MODEL_NAME, "prompt": prompt, "stream": False})
        response.raise_for_status()
        return response.json().get("response", "No response received")
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

def index_codebase(directory):
    index = CodeIndex()

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS]

        for file in files:
            file_path = os.path.join(root, file)

            print(f"🔍 Processing file: {file_path}")

            if not is_text_file(file_path):
                print(f"⚠️ Skipping non-text file: {file_path}")
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    if not content.strip():
                        print(f"⚠️ Skipping empty file: {file_path}")
                        continue

                    # **Check if the file contains a class definition**
                    if "class " in content:  # Basic check for class-based files
                        print(f"✅ Detected class file: {file_path}. Indexing full content.")
                        index.add(file_path, os.path.basename(file_path), content)
                        continue  # Skip function indexing since we added the full file

                    # Extract functions or methods
                    functions = extract_functions(content)
                    if functions:
                        for func_name, snippet in functions:
                            index.add(file_path, func_name, snippet)
                    else:
                        print(f"✅ No functions found in {file_path}. Indexing entire file.")
                        index.add(file_path, file, content)  # Index the entire file content

            except FileNotFoundError:
                print(f"⚠️ File not found: {file_path}. Skipping...")
            except PermissionError:
                print(f"⛔ Permission denied: {file_path}. Skipping...")
            except Exception as e:
                print(f"❌ Error reading {file_path}: {str(e)}")

    return index



def is_text_file(file_path, block_size=512):
    """Detect if a file is a text file or binary."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(block_size)
        if b"\x00" in chunk:  # If it contains null bytes, it's binary
            return False
        return True
    except Exception:
        return False  # Treat unreadable files as binary


def extract_functions(content):
    """Extract function and class names with their definitions from Laravel (PHP), Python, and JavaScript files."""
    snippets = []

    # PHP functions and methods (Laravel specific)
    php_pattern = r"(?:(public|protected|private)?\s*function\s+(\w+)\s*\(.*\)\s*\{|\s*public\s*function\s+(\w+)\s*\(.*\)\s*\{)"
    for match in re.findall(php_pattern, content):
        # Check if it's a function match
        if match[1]:
            snippets.append((match[1], match[0]))  # match[1] = function name, match[0] = full snippet
        elif match[2]:  # Laravel controller action
            snippets.append((match[2], match[0]))  # match[2] = function name, match[0] = full snippet

    # Python Functions & Classes
    python_pattern = r"(?:(def\s+(\w+)\s*\(.*\):\s*(?:\n\s{4,}.*)+)|(?:class\s+(\w+)\s*\(.*\):))"
    for match in re.findall(python_pattern, content):
        if match[1]:  # Python functions
            snippets.append((match[1], match[0]))
        elif match[2]:  # Python classes
            snippets.append((match[2], match[0]))

    # JavaScript Functions (named & class methods)
    js_pattern = r"(?:(function\s+(\w+)\s*\(.*\)\s*\{)|(?:class\s+(\w+)\s*\{.*\}))"
    for match in re.findall(js_pattern, content):
        if match[1]:  # Named functions
            snippets.append((match[1], match[0]))
        elif match[2]:  # Class methods
            snippets.append((match[2], match[0]))

    if not snippets:
        print("⚠️ No functions or classes found in this file.")  # Debugging
    return snippets


# Intelligent Query Processing
def process_query(query, code_index):
    """Find relevant code snippets and analyze only necessary parts"""
    
    # Search for direct matches (specific function or class)
    matches = code_index.search(query)

    if not matches:
        print("\n⚠️ No direct match found. Trying fuzzy matching...")
        matches = code_index.search_fuzzy(query)

    if not matches:
        print("\n⚠️ No close matches found. Providing full codebase context to AI...")
        # If no matches are found, send full indexing and the query
        full_index = generate_full_index(code_index)
        prompt = f"Here is the full codebase index:\n\n{full_index}\n\nNow, address the following query:\n{query}"
        return generate_text(prompt)

    print(f"\n🔍 Found {len(matches)} relevant code snippets.")  # Debugging

    # Collect all snippets in a list
    all_snippets = []
    for function_name, file_path in matches.items():
        snippets = code_index.get_snippets(file_path)
        
        # Add snippets to the list
        all_snippets.extend(snippets)
    
    # Join all snippets into a single string, separated by newlines or other separators
    snippets_text = "\n\n".join(all_snippets)
    
    # Construct the final prompt with all snippets
    prompt = f"Here are the snippets from the codebase index:\n\n{snippets_text}\n\nNow, address the following query:\n{query}"
    
    # Send the full prompt to the AI
    return generate_text(prompt)

    # return "\n".join(responses)

def generate_full_index(code_index):
    """Generate a human-readable summary of the full codebase index"""
    full_index = ""
    for file_path, snippets in code_index.file_snippets.items():
        if not snippets:
            continue  # Skip files with no snippets

        full_index += f"\n📂 File: {file_path}\n"
        for snippet in snippets:
            if len(snippet) == 2:  # Ensure that snippet is a tuple (function_name, snippet)
                function_name, snippet_code = snippet
                full_index += f"🔹 Function: {function_name}\n{snippet_code}\n"
            # else:
            #     # print(f"⚠️ Skipping invalid snippet format: {snippet}")
    return full_index


# Interactive Mode
def interactive_mode(code_index):
    """Allow users to query the codebase dynamically"""
    while True:
        try:
            user_input = input("\n📝 Your Question: ")
            if user_input.strip().lower() == "exit":
                print("\n👋 Exiting interactive mode...")
                break

            # Fetch relevant functions
            response = process_query(user_input, code_index)
            print(response)

        except KeyboardInterrupt:
            print("\n\n👋 Session ended.")
            break

# Main Function
def main():
    parser = argparse.ArgumentParser(description="AI-powered project analysis with instant code search.")
    parser.add_argument("action", choices=["analyze"], help="Action to perform")
    parser.add_argument("path", help="Project directory path")
    parser.add_argument("--prompt", help="Initial prompt/query for the AI", type=str)

    args = parser.parse_args()
    check_ollama_and_setup()

    print("\n🔍 Indexing project files...")
    code_index = index_codebase(args.path)
    print("\n✅ Indexing Complete. Ready for queries.")

    if args.prompt:
        print(f"\n📝 Query received: {args.prompt}")
        response = process_query(args.prompt, code_index)
        print(response)

    # Always enter interactive mode after processing the prompt (if provided)
    interactive_mode(code_index)


if __name__ == "__main__":
    main()
