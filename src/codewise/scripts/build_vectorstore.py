# scripts/build_vectorstore.py

import glob
import ast
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


# ---------- UTILITY FUNCTIONS ----------

def extract_functions(source_code):
    """
    Extract function and class definitions from source code.
    Returns a list of dicts: {'name': ..., 'code': ...}
    """
    items = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return items  # return empty list if parsing fails

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, "lineno", 0)
            end = getattr(node, "end_lineno", start)
            name = getattr(node, "name", "<anon>")
            code_lines = source_code.splitlines()
            code = "\n".join(code_lines[start-1:end])
            items.append({"name": name, "code": code})
    return items

# ---------- MAIN SCRIPT ----------

def main():
    # Try to auto-discover the Flask package directory inside the repository.
    # Common layout: <repo>/data/flask/src/flask
    from pathlib import Path
    script_dir = Path(__file__).resolve().parent
    repo_root = None

    # Walk up a few levels and search for the expected path or for a flask package
    for p in [script_dir, *script_dir.parents[:6]]:
        candidate = p / "data" / "flask" / "src" / "flask"
        if candidate.exists():
            repo_root = str(candidate)
            break

    # Fallback: look for any 'flask/__init__.py' under these parents
    if repo_root is None:
        for p in [script_dir, *script_dir.parents[:6]]:
            matches = list(p.rglob("flask/__init__.py"))
            # prefer matches that are not under site-packages
            for m in matches:
                if "site-packages" not in str(m):
                    repo_root = str(m.parent)
                    break
            if repo_root:
                break

    if repo_root is None:
        # Last resort: use a relative default and let the later check fail clearly
        repo_root = "data/flask/src/flask"
    vectorstore_output = "vectorstores/flask_store"
    os.makedirs(vectorstore_output, exist_ok=True)

    print("Scanning Python files in:", repo_root)
    documents = []

    for path in glob.glob(f"{repo_root}/**/*.py", recursive=True):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        funcs = extract_functions(text)
        if funcs:
            for func in funcs:
                documents.append({
                    "text": func["code"],
                    "source": path,
                    "name": func["name"]
                })
        else:
            # fallback: use full file if no functions/classes
            documents.append({
                "text": text,
                "source": path,
                "name": None
            })

    print(f"Total documents/chunks to embed: {len(documents)}")
    if len(documents) == 0:
        raise SystemExit(
            f"No Python files found under {repo_root}.\n"
            "Please set `repo_root` to the correct package path or place the repository at the expected layout."
        )

    # ---------- CREATE EMBEDDINGS ----------
    print("Creating embeddings using OpenAIEmbeddings...")
    embeddings = OpenAIEmbeddings()  # make sure OPENAI_API_KEY is set

    # ---------- BUILD FAISS VECTOR STORE ----------
    print("Building FAISS vector store...")
    vectorstore = FAISS.from_texts([d["text"] for d in documents], embeddings, metadatas=documents)

    # ---------- SAVE VECTOR STORE ----------
    vectorstore.save_local(vectorstore_output)
    print(f"Vector store saved at {vectorstore_output}")

if __name__ == "__main__":
    main()
