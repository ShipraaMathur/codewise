import os
import json
import sys
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE other imports
load_dotenv()

# Add the 'src' directory to the Python path so we can import modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github import Github, Auth
from src.core.static_analyzer import analyze_file_changes
from src.review.llm_reviewer import get_review_for_code
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
pr_number = 5121  # An example PR from Flask with Python file changes.
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
        for node_name, source_code in affected_nodes.items():
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
