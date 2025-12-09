# src/codewise/evaluation/metrics.py
from typing import List, Dict, Tuple
from .schema import CommentDict
import difflib
import math
import json
import os

def text_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()

def match_ai_to_human(ai: CommentDict, human: CommentDict, sim_threshold: float = 0.65) -> bool:
    # path exact or suffix
    if ai["path"] and human["path"]:
        if ai["path"].endswith(human["path"]) or human["path"].endswith(ai["path"]):
            # exact line match -> strong hit
            if ai["line"] != -1 and human["line"] != -1 and ai["line"] == human["line"]:
                return True
            # otherwise use body similarity
            sim = text_similarity(ai["body"], human["body"])
            return sim >= sim_threshold
    # fallback to text similarity only
    sim = text_similarity(ai["body"], human["body"])
    return sim >= sim_threshold

def compute_pr_metrics(ai_comments: List[CommentDict], human_comments: List[CommentDict]) -> Dict:
    matched_human = set()
    matched_ai = set()
    for i, a in enumerate(ai_comments):
        for j, h in enumerate(human_comments):
            if j in matched_human:
                continue
            if match_ai_to_human(a, h):
                matched_ai.add(i)
                matched_human.add(j)
                break
    tp = len(matched_ai)
    fp = len(ai_comments) - tp
    fn = len(human_comments) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "ai_total": len(ai_comments),
        "human_total": len(human_comments)
    }
