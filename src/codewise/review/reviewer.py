# src/codewise/review/reviewer.py

from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI  # Or any LLM you are using
from typing import List

# Optional: set temperature, max tokens, etc.
llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0.7)

# Prompt template for RAG review
PROMPT_TEMPLATE = """
You are a code reviewer. You are given a code diff and related context (previous code and PR comments). 
Analyze the code carefully and provide actionable inline review comments.

Diff:
{diff}

Context:
{context}

Provide a list of concise, actionable review comments (1 per line).
"""

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["diff", "context"]
)

# Build an LLM chain
chain = LLMChain(llm=llm, prompt=prompt)


def generate_comments(diff: str, retrieval_context: str) -> List[str]:
    """
    Generates RAG-enhanced review comments for a given diff using LLM and retrieved context.
    Returns a list of strings (one comment per item).
    """
    output = chain.run(diff=diff, context=retrieval_context)

    # Split output into lines, remove empty lines
    comments = [line.strip() for line in output.split("\n") if line.strip()]
    return comments
