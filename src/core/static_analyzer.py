import ast

def parse_patch(patch_text):
    """
    Parses a patch file and yields the line number and content of added lines.
    """
    if not patch_text:
        return

    file_line_number = 0
    for line in patch_text.split('\n'):
        if line.startswith('@@'):
            parts = line.split(' ')
            if len(parts) > 2 and parts[2].startswith('+'):
                try:
                    file_line_number = int(parts[2].split(',')[0][1:])
                except (ValueError, IndexError):
                    file_line_number = 1
        elif line.startswith('+') and not line.startswith('+++'):
            yield (file_line_number, line[1:])
            file_line_number += 1
        elif not line.startswith('-'):
            file_line_number += 1

def find_enclosing_node(tree, line_number):
    """
    Finds the function or class AST node that encloses a given line number.
    Returns the node object itself, not just the name.
    """
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line)
            if start_line <= line_number <= end_line:
                return node
    return None

def get_node_source(file_content, node):
    """
    Extracts the full source code of an AST node from the file content.
    """
    # ast.unparse is the most reliable method (Python 3.9+)
    try:
        return ast.unparse(node)
    except AttributeError:
        # Fallback to get_source_segment for slightly older versions
        return ast.get_source_segment(file_content, node)

def analyze_file_changes(file_content, patch_text):
    """
    Orchestrates the analysis of a single file's changes.

    Args:
        file_content (str): The full content of the modified file.
        patch_text (str): The patch diff for the file.

    Returns:
        dict: A dictionary where keys are names of affected functions/classes
              and values are their full source code.
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return {} # Cannot analyze files with syntax errors

    added_lines = list(parse_patch(patch_text))
    
    affected_nodes = {}
    unique_node_objects = set()

    for line_num, _ in added_lines:
        node = find_enclosing_node(tree, line_num)
        if node and node not in unique_node_objects:
            unique_node_objects.add(node)
            node_source = get_node_source(file_content, node)
            affected_nodes[node.name] = node_source
            
    return affected_nodes