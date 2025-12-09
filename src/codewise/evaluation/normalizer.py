# src/codewise/evaluation/normalizer.py
import re
from typing import Dict, Any
from .schema import CommentDict

def normalize_path(path: str) -> str:
    if path.startswith("src/"):
        return path[4:]
    # remove leading repo name if present (e.g., 'flask/src/...')
    path = re.sub(r"^.*?/src/", "", path)
    return path

def normalize_comment(raw: Dict[str, Any]) -> CommentDict:
    body = raw.get("body", "")
    # strip markdown simple:
    body = re.sub(r"\s+```\s*.*?```", "", body, flags=re.S)
    body = re.sub(r"`(.+?)`", r"\1", body)
    body = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", body)
    body = body.strip()
    return {
        "path": normalize_path(raw.get("path","")),
        "line": int(raw.get("line", -1)),
        "body": body,
        "severity": raw.get("severity", "Unknown")
    }
