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
    repo_root = "data/flask/src/flask"  # path to the main Python package
    vectorstore_output = "vectorstores/flask_store"
    os.makedirs(vectorstore_output, exist_ok=True)

    print("Scanning Python files...")
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
