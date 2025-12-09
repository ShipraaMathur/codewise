import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Ensure the OPENAI_API_KEY is loaded from .env
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Missing OPENAI_API_KEY in .env!")

PROMPT_TEMPLATE = """
You are an expert Python code reviewer. Your role is to analyze the provided code snippet for bugs,
style violations (PEP 8), and potential improvements. Provide your feedback in the requested JSON format.

Tone: {tone}
Verbosity: {verbosity}

Here is the code snippet to review:
---
{source_code}
---

Relevant Project Context (retrieved from vectorstore):
---
{retrieved_context}
---

{format_instructions}
"""

# Define the desired data structure for the JSON output.
class ReviewComment(BaseModel):
    line_number: int = Field(description="The line number in the provided snippet where the issue is.")
    comment: str = Field(description="A concise, helpful comment explaining the issue and suggesting a fix.")
    severity: str = Field(description="A rating of 'High', 'Medium', or 'Low'.")

class Review(BaseModel):
    review_comments: list[ReviewComment] = Field(description="A list of review comments.", min_length=1)

def get_review_for_code(source_code: str, retrieved_context: str = "", temperature: float = 0.2, adaptation_params: dict | None = None) -> dict | None:
    """
    Generates AI-powered code review for a given source code snippet.

    Args:
        source_code (str): The source code of the function/class to review.
        temperature (float): The temperature setting for the LLM.

    Returns:
        A dictionary containing the structured review comments, or None if no issues are found.
    """
    try:
        # Set up a parser + inject instructions into the prompt template.
                # Default adaptation if none provided
        if adaptation_params is None:
            adaptation_params = {"tone": "neutral", "verbosity": "medium"}

        tone = adaptation_params.get("tone", "neutral")
        verbosity = adaptation_params.get("verbosity", "medium")
        parser = JsonOutputParser(pydantic_object=Review)

        prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["source_code","retrieved_context","tone","verbosity"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        model = ChatOpenAI(model="gpt-4o", temperature=temperature)

        chain = prompt | model | parser
        
        return chain.invoke({"source_code": source_code, "retrieved_context": retrieved_context, "tone": tone, "verbosity": verbosity})
    except Exception as e:
        # If the LLM says there are no issues, it might return a non-JSON response.
        # Or if another error occurs.
        print(f"  [INFO] Could not generate or parse review. This might mean no issues were found. Error: {e}")
        return None