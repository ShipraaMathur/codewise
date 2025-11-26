import os
import ast
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

if not token:
    raise ValueError("Missing GITHUB_TOKEN in .env!")

g = Github(auth=Auth.Token(token))

repo = g.get_repo("pallets/flask")   # Example repo

print("Connected to:", repo.full_name)

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

# --- Main Logic ---
# For development, we target a single, known PR.
pr_number = 5121  # An example PR from Flask with Python file changes.
pr = repo.get_pull(pr_number)

print(f"\nProcessing PR #{pr.number}: {pr.title}")

for file in pr.get_files():
    if not file.filename.endswith(".py"):
        continue

    print(f"\n--- Analyzing file: {file.filename} ---")
    
    # 1. Get the full content of the file from the PR's head commit
    file_content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode("utf-8")
    
    # 2. Parse the file content into an Abstract Syntax Tree (AST)
    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        print(f"  Could not parse AST for {file.filename}: {e}")
        continue

    # 3. Parse the patch to get added lines and their line numbers
    added_lines = list(parse_patch(file.patch))

    # 4. Map added lines to the functions/classes they belong to
    affected_nodes = {}
    for line_num, line_content in added_lines:
        node_name = find_enclosing_node(tree, line_num)
        if node_name:
            if node_name not in affected_nodes:
                affected_nodes[node_name] = []
            affected_nodes[node_name].append(f"+{line_num}: {line_content}")

    # 5. Print the results
    if not affected_nodes:
        print("  No changes detected within a function or class.")
    else:
        for node_name, changes in affected_nodes.items():
            print(f"  Affected node '{node_name}':")
            for change in changes:
                print(f"    {change}")
