import os
import ast
import json
from github import Github, Auth
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import sys

sys.path.append(os.path.abspath("."))  # Add project root to path
from codewise.github_test import parse_patch, find_enclosing_node

# -------------------------------
# Config
# -------------------------------
load_dotenv()
token = os.getenv("GITHUB_TOKEN")
if not token:
    raise ValueError("Missing GITHUB_TOKEN in .env!")

PR_NUMBER = 5121  # Example PR number
TOP_K = 5         # Number of top matches to retrieve
OUTPUT_JSON = "pr_retrieval_output.json"

# -------------------------------
# Connect to GitHub
# -------------------------------
g = Github(auth=Auth.Token(token))
repo = g.get_repo("pallets/flask")
print("Connected to:", repo.full_name)

# -------------------------------
# Load FAISS vector stores
# -------------------------------
embeddings = OpenAIEmbeddings()
code_store_path = "vectorstores/flask_store"
comments_store_path = "vectorstores/pr_comments_store"

code_store = FAISS.load_local(
    code_store_path, embeddings=embeddings, allow_dangerous_deserialization=True
)
comments_store = FAISS.load_local(
    comments_store_path, embeddings=embeddings, allow_dangerous_deserialization=True
)

# -------------------------------
# Retrieval function
# -------------------------------
def retrieve_context(code_snippet: str, top_k: int = TOP_K):
    """Retrieve top-k relevant code fragments and PR comments for a code snippet."""
    code_matches = code_store.similarity_search(code_snippet, k=top_k)
    pr_comments = comments_store.similarity_search(code_snippet, k=top_k)
    return code_matches, pr_comments

# -------------------------------
# Process PR
# -------------------------------
pr = repo.get_pull(PR_NUMBER)
print(f"\nProcessing PR #{pr.number}: {pr.title}")

pr_output = {
    "pr_number": pr.number,
    "pr_title": pr.title,
    "files": []
}

for file in pr.get_files():
    if not file.filename.endswith(".py"):
        continue

    print(f"\n--- Analyzing file: {file.filename} ---")
    
    file_output = {"filename": file.filename, "nodes": []}

    # Get file content
    file_content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode("utf-8")
    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        print(f"Skipping {file.filename}: AST parse error: {e}")
        continue

    # Parse added lines and map to nodes
    added_lines = list(parse_patch(file.patch))
    affected_nodes = {}
    for line_num, line_content in added_lines:
        node_name = find_enclosing_node(tree, line_num)
        if node_name:
            affected_nodes.setdefault(node_name, []).append(f"+{line_num}: {line_content}")

    # Retrieve context for each affected node
    for node_name, lines in affected_nodes.items():
        modified_code = "\n".join(line.split(": ", 1)[1] for line in lines)
        print(f"\n=== Node: {node_name} in {file.filename} ===\n")

        code_matches, pr_comments = retrieve_context(modified_code, top_k=TOP_K)

        # --- Print Top Code Matches ---
        print("Top Code Matches:")
        code_output = []
        for i, match in enumerate(code_matches, 1):
            snippet = match.page_content[:500].replace("\n", " ")
            print(f"{i}. {snippet}...\n{'-'*40}")
            code_output.append({"rank": i, "content": match.page_content, "metadata": getattr(match, "metadata", {})})

        # --- Print Top PR Comments ---
        print("\nTop PR Comments:")
        comments_output = []
        for i, comment in enumerate(pr_comments, 1):
            meta = comment.metadata if hasattr(comment, "metadata") else {}
            source_file = meta.get("file", "unknown")
            text = comment.page_content if hasattr(comment, "page_content") else str(comment)
            snippet = text[:300].replace("\n", " ")
            print(f"{i}. {source_file}: {snippet}...\n{'-'*40}")
            comments_output.append({"rank": i, "content": text, "metadata": meta})

        # Add to file output
        file_output["nodes"].append({
            "node_name": node_name,
            "added_lines": lines,
            "top_code_matches": code_output,
            "top_pr_comments": comments_output
        })

    pr_output["files"].append(file_output)

# -------------------------------
# Save JSON output
# -------------------------------
with open(OUTPUT_JSON, "w") as f:
    json.dump(pr_output, f, indent=2)

print(f"\n✅ JSON output saved to {OUTPUT_JSON}")
