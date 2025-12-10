# src/codewise/evaluation/metrics.py
from typing import List, Dict, Tuple
from .schema import CommentDict
import difflib
import math
import json
import os

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False

def text_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()

import re

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were",
    "should", "could", "would", "might", "may",
    "to", "of", "and", "or", "but", "if", "then",
    "this", "that", "for", "on", "in", "with",
    "be", "as", "it", "its", "at", "by", "from",
}

def extract_core_words(text: str):
    text = text.lower()
    tokens = re.findall(r"[a-zA-Z]+", text)
    return [t for t in tokens if t not in STOPWORDS]

def semantic_overlap(ai_body: str, human_body: str) -> float:
    """
    Semantic similarity using ROUGE-L (longest common subsequence F-score).
    For RAG evaluation, this measures semantic similarity better than keyword matching.
    
    Falls back to keyword matching if rouge-score not available.
    """
    if not ROUGE_AVAILABLE:
        # Fallback: keyword matching
        ai_words = set(extract_core_words(ai_body))
        human_words = set(extract_core_words(human_body))

        if not human_words:
            return 0.0

        common = ai_words.intersection(human_words)
        return len(common) / len(human_words)
    
    # Use ROUGE-L metric (longest common subsequence with F-score)
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(human_body, ai_body)
    return scores['rougeL'].fmeasure

def match_ai_to_human(ai: CommentDict, human: CommentDict, overlap_threshold: float = 0.2) -> bool:
    # 1. File must match (suffix or exact)
    if ai["path"] and human["path"]:
        if not (
            ai["path"].endswith(human["path"]) or 
            human["path"].endswith(ai["path"])
        ):
            return False

    # 2. Exact line match = auto match
    if ai["line"] != -1 and human["line"] != -1:
        if ai["line"] == human["line"]:
            return True

    # 3. Semantic overlap check
    overlap = semantic_overlap(ai["body"], human["body"])
    return overlap >= overlap_threshold


def compute_pr_metrics(ai_comments: List[CommentDict], human_comments: List[CommentDict]) -> Dict:
    """
    Compute ROUGE-L scores for RAG evaluation.
    For each AI comment, calculates max ROUGE-L F-score against all human comments.
    Returns average ROUGE score across all AI comments.
    
    If human_comments is empty, returns "no_ground_truth" flag (instead of zeros) so the dashboard
    can show "Ground truth not available" rather than misleading 0% scores.
    """
    result = {
        "ai_total": len(ai_comments),
        "human_total": len(human_comments)
    }
    
    # If no AI comments or no human comments, mark as no ground-truth available
    if not ai_comments:
        result.update({
            "rouge_l_avg": None,
            "rouge_l_max": None,
            "rouge_l_min": None,
            "no_ground_truth": True,
            "reason": "No AI comments generated"
        })
        return result
    
    if not human_comments:
        result.update({
            "rouge_l_avg": None,
            "rouge_l_max": None,
            "rouge_l_min": None,
            "no_ground_truth": True,
            "reason": "No human ground-truth comments available (not found on GitHub or in ground_truth.json)"
        })
        return result
    
    # Both AI and human comments are present; compute ROUGE scores
    rouge_scores = []
    for ai in ai_comments:
        max_score = semantic_overlap(ai["body"], human_comments[0]["body"]) if human_comments else 0.0
        for human in human_comments:
            score = semantic_overlap(ai["body"], human["body"])
            max_score = max(max_score, score)
        rouge_scores.append(max_score)
    
    avg_score = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0.0
    max_score = max(rouge_scores) if rouge_scores else 0.0
    min_score = min(rouge_scores) if rouge_scores else 0.0

    result.update({
        "rouge_l_avg": avg_score,
        "rouge_l_max": max_score,
        "rouge_l_min": min_score,
        "no_ground_truth": False
    })
    return result
