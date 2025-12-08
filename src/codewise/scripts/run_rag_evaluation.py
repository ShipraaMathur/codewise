#!/usr/bin/env python3
"""
Run RAG evaluation harness.

By default this uses mock baseline & RAG reviewers (no external API calls) so you can test the pipeline.
To use real reviewers:
  - import your reviewer functions and replace mock_baseline_reviewer / mock_rag_reviewer, or
  - modify run_evaluation() to call your modules.
"""

import json
from pathlib import Path
import sys
import os
from dotenv import load_dotenv
load_dotenv()
# Ensure the top-level `src` directory is on `sys.path` when running
# this script directly from the repository root so `import codewise`
# finds the package (package lives in `src/codewise`).
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from codewise.core import evaluation as eval_mod
from codewise.retriever.retriever_client import get_retrieval_context
from codewise.review.reviewer import generate_comments  # Make sure this function exists and returns List[str]

# --- Baseline reviewer (can be static, or another LLM) ---
def baseline_reviewer(pr):
    # Use the old mock baseline for now
    return [
        "Consider adding a docstring.",
        "Use a better variable name."
    ]

# --- RAG reviewer using retrieval ---
def rag_reviewer(pr):
    diff = pr['diff']
    retrieval_context = get_retrieval_context(diff, top_k=5)
    # generate_comments(diff, context) should return List[str]
    return generate_comments(diff, retrieval_context)

# --- Evaluation harness ---
def run_evaluation(prs, ground_truth_map, output_csv_path):
    results = []
    for pr in prs:
        pr_id = pr.get('id', pr.get('pr_number', 'unknown'))

        # Baseline
        baseline_comments = baseline_reviewer(pr)

        # RAG
        rag_comments = rag_reviewer(pr)

        gt = ground_truth_map.get(str(pr_id), [])
        result = eval_mod.evaluate_pair(baseline_comments, rag_comments, gt)
        results.append({'pr_id': pr_id, 'result': result})

    eval_mod.save_results_csv(results, output_csv_path)
    return results


if __name__ == '__main__':
    # Example PRs for demo; replace with real PRs later
    prs = [
        {'id': 1, 'title': 'Fix session expiry bug', 'diff': 'def delete_expired_sessions(): ...'},
        {'id': 2, 'title': 'Refactor auth module', 'diff': 'def refresh_token(): ...'},
        {'id': 3, 'title': 'Remove unused import', 'diff': 'import os\nimport sys'}
    ]

    # Ground truth keywords
    gt_map = {
        "1": ["session", "expiry", "delete_expired_sessions"],
        "2": ["auth", "token", "refactor"],
        "3": ["unused import", "dead code"]
    }

    out_csv = Path('codewise_evaluation/rag_eval_results.csv')
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    results = run_evaluation(prs, gt_map, str(out_csv))
    print("Evaluation complete. Results saved to:", out_csv)
    print(json.dumps(results, indent=2))