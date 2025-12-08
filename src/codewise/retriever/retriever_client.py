import os
from typing import Optional

# We import FAISS and embeddings lazily because FAISS is an optional
# dependency that may not be available (especially on macOS/arm64).
# Loading the vectorstores at import time caused import-time failures
# if `faiss` wasn't installed. The functions below will attempt to
# initialize stores on first use and otherwise return an empty context.

CODE_STORE_PATH = "vectorstores/flask_store"
COMMENTS_STORE_PATH = "vectorstores/pr_comments_store"

# Globals populated on-demand
code_store = None
comments_store = None
embeddings = None


def _ensure_stores_loaded() -> None:
    """Attempt to import FAISS and load persisted vectorstores.

    If FAISS or the vectorstores can't be loaded, leave stores as None
    so callers can handle the missing retriever gracefully.
    """
    global code_store, comments_store, embeddings
    if code_store is not None and comments_store is not None:
        return

    # Allow an environment variable to explicitly disable the retriever
    if os.environ.get("DISABLE_RETRIEVER", "0") in ("1", "true", "True"):
        return

    try:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
    except Exception:
        # faiss (or related libs) not available — leave stores as None
        return

    try:
        embeddings = OpenAIEmbeddings()
        code_store = FAISS.load_local(
            CODE_STORE_PATH,
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )
        comments_store = FAISS.load_local(
            COMMENTS_STORE_PATH,
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )
    except Exception:
        # Loading vectorstores failed (corrupt files, incompatible FAISS),
        # keep stores as None and allow the application to continue.
        code_store = None
        comments_store = None


def get_retrieval_context(code_snippet: str, top_k: int = 5) -> str:
    """
    Returns combined code + PR comment retrieval context
    as a single formatted string suitable for LLM prompts.
    """

    # Ensure stores are loaded; if unavailable, return an empty context.
    _ensure_stores_loaded()
    if code_store is None or comments_store is None:
        return ""

    code_matches = code_store.similarity_search(code_snippet, k=top_k)
    comment_matches = comments_store.similarity_search(code_snippet, k=top_k)

    # Build readable context
    context_blocks = ["# Relevant Code Snippets:"]
    for m in code_matches:
        context_blocks.append(m.page_content)

    context_blocks.append("\n# Relevant PR Comments:")
    for c in comment_matches:
        context_blocks.append(c.page_content)

    return "\n\n---\n\n".join(context_blocks)