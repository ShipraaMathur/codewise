# src/codewise/evaluation/schema.py
from typing import TypedDict, List, Dict, Any

class CommentDict(TypedDict):
    path: str
    line: int
    body: str
    severity: str

class PRData(TypedDict):
    pr_id: int
    diff: str
    ground_truth_comments: List[CommentDict]
    ai_comments: List[CommentDict]
    meta: Dict[str, Any]
