import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load vectorstores once at module import
embeddings = OpenAIEmbeddings()

CODE_STORE_PATH = "vectorstores/flask_store"
COMMENTS_STORE_PATH = "vectorstores/pr_comments_store"

code_store = FAISS.load_local(
    CODE_STORE_PATH,
    embeddings=embeddings,
    allow_dangerous_deserialization=True
)

comments_store = FAISS.load_local(
    COMMENTS_STORE_PATH,
    embeddings=embeddings,
    allow_dangerous_deserialization=True
)


def get_retrieval_context(code_snippet: str, top_k: int = 5) -> str:
    """
    Returns combined code + PR comment retrieval context
    as a single formatted string suitable for LLM prompts.
    """

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