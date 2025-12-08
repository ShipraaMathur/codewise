import csv
import json
from typing import List, Dict, Any
from pathlib import Path

def score_comment_against_ground_truth(comment: str, ground_truth: List[str]) -> float:
    """
    Simple heuristic scoring:
      - Score = fraction of ground-truth keywords that appear in the comment (case-insensitive).
    This is intentionally conservative and explainable; you can replace it with a learned metric
    (BLEU-like, embedding similarity, or human annotation) if you have ground-truth labels.
    """
    comment_lower = comment.lower()
    if not ground_truth:
        return 0.0
    matched = 0
    for gt in ground_truth:
        if gt.lower() in comment_lower:
            matched += 1
    return matched / len(ground_truth)

def evaluate_pair(baseline_comments: List[str], rag_comments: List[str], ground_truth_issues: List[str]) -> Dict[str, Any]:
    """
    Evaluate baseline vs RAG outputs for a single PR.
    Returns dict with aggregated scores and raw comments.
    """
    baseline_scores = [score_comment_against_ground_truth(c, ground_truth_issues) for c in baseline_comments]
    rag_scores = [score_comment_against_ground_truth(c, ground_truth_issues) for c in rag_comments]

    def aggregate(scores):
        return {
            'count': len(scores),
            'mean_score': (sum(scores)/len(scores)) if scores else 0.0,
            'max_score': max(scores) if scores else 0.0
        }

    return {
        'baseline': aggregate(baseline_scores),
        'rag': aggregate(rag_scores),
        'baseline_comments': baseline_comments,
        'rag_comments': rag_comments,
        'ground_truth_count': len(ground_truth_issues)
    }

def save_results_csv(results: List[Dict[str, Any]], csv_path: str):
    """
    Save a compact CSV summarizing each PR comparison.
    CSV fields:
      - pr_id
      - baseline_count
      - baseline_mean_score
      - baseline_max_score
      - rag_count
      - rag_mean_score
      - rag_max_score
      - ground_truth_count
    """
    fieldnames = [
        'pr_id',
        'baseline_count', 'baseline_mean_score', 'baseline_max_score',
        'rag_count', 'rag_mean_score', 'rag_max_score',
        'ground_truth_count'
    ]
    p = Path(csv_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {
                'pr_id': r['pr_id'],
                'baseline_count': r['result']['baseline']['count'],
                'baseline_mean_score': round(r['result']['baseline']['mean_score'], 4),
                'baseline_max_score': round(r['result']['baseline']['max_score'], 4),
                'rag_count': r['result']['rag']['count'],
                'rag_mean_score': round(r['result']['rag']['mean_score'], 4),
                'rag_max_score': round(r['result']['rag']['max_score'], 4),
                'ground_truth_count': r['result']['ground_truth_count']
            }
            writer.writerow(row)

def load_ground_truth(gt_path: str) -> Dict[str, List[str]]:
    """
    Load a JSON mapping of PR id -> list of ground truth keywords/issues.
    Example:
      {
        "1": ["session", "expiry", "delete_expired_sessions"],
        "2": ["auth", "token", "refactor"]
      }
    """
    p = Path(gt_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())
