# src/codewise/evaluation/loaders.py
import json
import os
from typing import List, Dict, Any
from .schema import PRData, CommentDict

LOG_PATH = os.path.join(os.getcwd(), "src", "logs", "feedback.json")

def load_ai_comments() -> Dict[int, List[CommentDict]]:
    """Return mapping pr_number -> list[normalized comment dicts]."""
    if not os.path.exists(LOG_PATH):
        raise FileNotFoundError(f"{LOG_PATH} not found")
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    out: Dict[int, List[CommentDict]] = {}
    for entry in data:
        pr = int(entry.get("pr_number"))
        # review field is stringified JSON
        review_json = entry.get("review")
        try:
            review = json.loads(review_json)
        except Exception:
            review = {}
        comments = []
        for c in review.get("review_comments", []):
            comments.append({
                "path": entry.get("file") or c.get("file") or "",
                "line": int(c.get("line_number", -1)),
                "body": c.get("comment", "").strip(),
                "severity": c.get("severity", "Unknown")
            })
        out.setdefault(pr, []).extend(comments)
    return out

# Optional: fetch human comments from GitHub using your client.
def fetch_human_comments_from_github(github_client, owner_repo:str, pr_number:int) -> List[CommentDict]:
    """
    github_client must expose get_pr_comments(owner_repo, pr_number) -> list of pygithub Comment objects or dicts
    """
    raw = github_client.get_pr_review_comments(owner_repo, pr_number)
    comments = []
    for r in raw:
        # adapt to your github_client return value
        path = r.get("path") or getattr(r, "path", "")
        line = r.get("line") or r.get("position") or getattr(r, "line", -1)
        body = r.get("body") or getattr(r, "body", "")
        comments.append({"path": path, "line": int(line) if line is not None else -1, "body": body.strip(), "severity": "Human"})
    return comments

def build_prdata(pr_number:int, github_client=None, owner_repo: str = "pallets/flask") -> PRData:
    """Construct PRData for a single PR number."""
    ai_map = load_ai_comments()
    ai_comments = ai_map.get(pr_number, [])

    diff_text = ""
    if github_client is not None:
        pr_files = github_client.get_pr_files(owner_repo, pr_number)
        # combine file patches as the "diff" string
        patches = []
        for f in pr_files:
            patches.append(f.get("patch") or "")
        diff_text = "\n".join(patches)

    # If no github_client, caller can fill ground_truth_comments manually
    human_comments = []
    if github_client is not None:
        human_comments = fetch_human_comments_from_github(github_client, owner_repo, pr_number)

    return PRData(
        pr_id=pr_number,
        diff=diff_text,
        ground_truth_comments=human_comments,
        ai_comments=ai_comments,
        meta={"owner_repo": owner_repo}
    )
