# src/codewise/evaluation/evaluator.py
import json
import os
from typing import List
from .loaders import build_prdata, load_ai_comments
from .normalizer import normalize_comment
from .metrics import compute_pr_metrics
from .schema import PRData
from src.codewise.github_client import GitHubClient as gc_mod
 # adapt if different import path

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "evaluation_results")

def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)

def normalize_list(lst):
    return [normalize_comment(c) for c in lst]

def evaluate_pr(pr_number: int, github_client=None, owner_repo="pallets/flask") -> dict:
    prdata = build_prdata(pr_number, github_client=github_client, owner_repo=owner_repo)
    ai_norm = normalize_list(prdata["ai_comments"])
    human_norm = normalize_list(prdata["ground_truth_comments"])
    metrics = compute_pr_metrics(ai_norm, human_norm)
    result = {
        "pr_id": pr_number,
        "metrics": metrics,
        "ai_count": len(ai_norm),
        "human_count": len(human_norm)
    }
    return result

def evaluate_many(pr_list: List[int], github_client=None, owner_repo="pallets/flask") -> dict:
    ensure_results_dir()
    per_pr = []
    rouge_scores = []
    for pr in pr_list:
        r = evaluate_pr(pr, github_client=github_client, owner_repo=owner_repo)
        per_pr.append(r)
        m = r["metrics"]
        rouge_scores.append(m.get("rouge_l_avg", 0.0))
    
    avg_rouge = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0.0
    max_rouge = max(rouge_scores) if rouge_scores else 0.0
    min_rouge = min(rouge_scores) if rouge_scores else 0.0

    summary = {
        "overall": {"rouge_l_avg": avg_rouge, "rouge_l_max": max_rouge, "rouge_l_min": min_rouge},
        "per_pr": per_pr
    }

    # save files
    with open(os.path.join(RESULTS_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(summary["overall"], f, indent=2)
    with open(os.path.join(RESULTS_DIR, "per_pr_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(summary["per_pr"], f, indent=2)
    return summary
