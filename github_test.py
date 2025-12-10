import os
import json
import sys
from dotenv import load_dotenv
import ast
from github import Github, Auth

# Load environment variables from .env file BEFORE other imports
load_dotenv()

# Add the 'src' directory to the Python path so we can import modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github import Github, Auth
from src.codewise.core.static_analyzer import analyze_file_changes
from src.codewise.review.llm_reviewer import get_review_for_code
token = os.getenv("GITHUB_TOKEN")

if not token:
    raise ValueError("Missing GITHUB_TOKEN in .env!")

g = Github(auth=Auth.Token(token))
# Ensure the OPENAI_API_KEY is loaded for the reviewer module
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Missing OPENAI_API_KEY in .env!")

repo = g.get_repo("pallets/flask")   # Example repo

print("Connected to:", repo.full_name)

# --- Main Logic ---
# For development, we target a single, known PR.
import os
import argparse

# Allow PR number to be provided via env var or CLI argument
def get_pr_number():
    pr_from_env = os.environ.get("PR_NUMBER")
    if pr_from_env:
        try:
            return int(pr_from_env)
        except ValueError:
            pass
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--pr", type=int, help="PR number to test")
    args, _ = parser.parse_known_args()
    if args.pr:
        return int(args.pr)
    return 5853  # default example PR

pr_number = get_pr_number()
pr = repo.get_pull(pr_number)

print(f"\nProcessing PR #{pr.number}: {pr.title}")

for file in pr.get_files():
    if not file.filename.endswith(".py"):
        continue

    print(f"\n--- Analyzing file: {file.filename} ---")

    try:
        # 1. Get file content and patch text
        file_content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode("utf-8")
        patch_text = file.patch
        
        # 2. Analyze the changes to get affected functions/classes and their source
        affected_nodes = analyze_file_changes(file_content, patch_text)

        # 3. Print the results
        for node_name, node_info in affected_nodes.items():
            source_code = node_info["source_code"]
            print(f"  Affected node '{node_name}':")
            print("    --- Source Code ---")
            # Indent source code for better readability
            print("\n".join([f"    {line}" for line in source_code.splitlines()]))
            print("    -------------------")

            # 4. Get AI-powered review for the source code
            print("    --- AI Review ---")
            review = get_review_for_code(source_code)
            # Pretty-print the JSON review
            print(json.dumps(review, indent=4))
            print("    -----------------\n")

    except Exception as e:
        print(f"  Could not analyze file {file.filename}: {e}")
        continue


def parse_patch(patch_text):
    """
    Parses a patch file and yields the line number and content of added lines.
    """
    if not patch_text:
        return

    file_line_number = 0
    for line in patch_text.split('\n'):
        if line.startswith('@@'):
            # Extract the starting line number for the new file from the hunk header
            # e.g., @@ -30,7 +30,9 @@
            parts = line.split(' ')
            if len(parts) > 2 and parts[2].startswith('+'):
                try:
                    file_line_number = int(parts[2].split(',')[0][1:])
                except (ValueError, IndexError):
                    # If parsing fails, it might be a file creation; line number is 1
                    file_line_number = 1
        elif line.startswith('+') and not line.startswith('+++'):
            # This is an added line
            yield (file_line_number, line[1:])
            file_line_number += 1
        elif not line.startswith('-'):
            # This is a context line or a hunk header, increment line number
            file_line_number += 1

def find_enclosing_node(tree, line_number):
    """
    Finds the function or class that encloses a given line number by walking the AST.
    """
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno
            # Use end_lineno if available (Python 3.8+), otherwise it's less accurate
            end_line = getattr(node, 'end_lineno', start_line)

            if start_line <= line_number <= end_line:
                return node.name
    return None # No enclosing function/class found
