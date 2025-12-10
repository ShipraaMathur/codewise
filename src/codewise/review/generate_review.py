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
from codewise.core.static_analyzer import analyze_file_changes
from codewise.review.llm_reviewer import get_review_for_code
from codewise.retriever.retriever_client import get_retrieval_context
from codewise.review.feedback_logger import FeedbackLogger


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
    feedback_logger = FeedbackLogger()
    adaptation_params = feedback_logger.compute_adaptation_params(pr_number)

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

            for node_name, node_data in affected_nodes.items():
                source_code = node_data["source_code"]
                added_lines = node_data.get("added_lines", [])
                
                retrieval_context = get_retrieval_context(source_code)

                review = get_review_for_code(
                    source_code,
                    retrieved_context=retrieval_context,
                    temperature=args.temperature,
                    adaptation_params=adaptation_params
                )

                if review:
                    if isinstance(review, dict):
                        review_str = json.dumps(review)
                    else:
                        review_str = str(review)
                    # Default line number = None if no added lines exist
                    line_number = added_lines[0][0] if added_lines else None

                    file_review["reviews"].append({
                        "node": node_name,
                        "review": review,
                        "file_path": file.filename,
                        "line_number": line_number
                    })
                    feedback_logger.add_feedback(
                        pr_number=pr_number,
                        file_name=file.filename,
                        node_name=node_name,
                        review_text=review_str
                    )
            if file_review["reviews"]:
                full_review["files"].append(file_review)

        except Exception as e:
            print(f"Could not analyze file {file.filename}: {e}", file=sys.stderr)

    # Print the final combined review as a single JSON string
    print(json.dumps(full_review, indent=2))
    feedback_logger.save_json()

if __name__ == "__main__":
    main()