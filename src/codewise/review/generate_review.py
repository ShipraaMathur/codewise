import os
import sys
import argparse
import json
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path to allow imports from 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from github import Github, Auth
from src.codewise.core.static_analyzer import analyze_file_changes
from src.codewise.review.llm_reviewer import get_review_for_code

def parse_pr_url(pr_url: str) -> tuple[str, int]:
    """Parses a GitHub PR URL to get the repo name and PR number."""
    path_parts = urlparse(pr_url).path.strip('/').split('/')
    if len(path_parts) < 4 or path_parts[2] != 'pull':
        raise ValueError("Invalid GitHub PR URL format. Expected format: https://github.com/owner/repo/pull/123")
    
    repo_name = f"{path_parts[0]}/{path_parts[1]}"
    pr_number = int(path_parts[3])
    return repo_name, pr_number

def main():
    parser = argparse.ArgumentParser(description="Generate a code review for a GitHub Pull Request.")
    parser.add_argument("--pr-url", required=True, help="The full URL of the pull request to review.")
    parser.add_argument("--temperature", type=float, default=0.2, help="The temperature setting for the LLM.")
    args = parser.parse_args()

    # --- GitHub Setup ---
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("Missing GITHUB_TOKEN in .env!")
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Missing OPENAI_API_KEY in .env!")

    try:
        repo_name, pr_number = parse_pr_url(args.pr_url)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    g = Github(auth=Auth.Token(token))
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # --- Review Generation ---
    full_review = {"pr_title": pr.title, "files": []}

    for file in pr.get_files():
        if not file.filename.endswith(".py"):
            continue

        try:
            file_content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode("utf-8")
            patch_text = file.patch
            affected_nodes = analyze_file_changes(file_content, patch_text)

            file_review = {"filename": file.filename, "reviews": []}

            for node_name, source_code in affected_nodes.items():
                review = get_review_for_code(source_code, temperature=args.temperature) # This was already correct, but depends on the change below
                if review:
                    file_review["reviews"].append({"node": node_name, "review": review})
            
            if file_review["reviews"]:
                full_review["files"].append(file_review)

        except Exception as e:
            print(f"Could not analyze file {file.filename}: {e}", file=sys.stderr)

    # Print the final combined review as a single JSON string
    print(json.dumps(full_review, indent=2))

if __name__ == "__main__":
    main()