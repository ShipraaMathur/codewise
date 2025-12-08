#!/usr/bin/env python3
"""
Plot Baseline vs RAG evaluation results.
Generates:
  - Line chart: mean score per PR
  - Optional heatmap: baseline vs RAG per PR
"""

import argparse
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def _find_repo_root_with_eval_dir() -> Path:
    p = Path(__file__).resolve().parent
    # Walk up to 6 levels looking for `codewise_evaluation`
    for _ in range(6):
        candidate = p
        if (candidate / 'codewise_evaluation').exists():
            return candidate
        if p.parent == p:
            break
        p = p.parent
    # fallback: use three parents up (best-effort)
    return Path(__file__).resolve().parent.parents[3]


REPO_ROOT = _find_repo_root_with_eval_dir()
CSV_PATH = REPO_ROOT / 'codewise_evaluation' / 'rag_eval_results.csv'
OUT_LINE_PNG = REPO_ROOT / 'codewise_evaluation' / 'rag_eval_line.png'
OUT_HEATMAP_PNG = REPO_ROOT / 'codewise_evaluation' / 'rag_eval_heatmap.png'


def plot_line_chart(csv_path: str, out_png: str):
    prs, baseline_means, rag_means = [], [], []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            prs.append(row['pr_id'])
            baseline_means.append(float(row['baseline_mean_score']))
            rag_means.append(float(row['rag_mean_score']))

    plt.figure(figsize=(8, 4))
    plt.plot(prs, baseline_means, marker='o', label='Baseline mean score')
    plt.plot(prs, rag_means, marker='o', label='RAG mean score')
    plt.xlabel('PR ID')
    plt.ylabel('Mean helpfulness score')
    plt.title('Baseline vs RAG mean helpfulness per PR')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png)
    plt.close()
    print("Line chart saved to", out_png)


def plot_heatmap(csv_path: str, out_png: str):
    prs, baseline_means, rag_means = [], [], []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            prs.append(row['pr_id'])
            baseline_means.append(float(row['baseline_mean_score']))
            rag_means.append(float(row['rag_mean_score']))

    data = np.array([baseline_means, rag_means])
    fig, ax = plt.subplots(figsize=(8, 4))
    cax = ax.imshow(data, cmap='viridis', aspect='auto')

    ax.set_yticks([0, 1])
    ax.set_yticklabels(['Baseline', 'RAG'])
    ax.set_xticks(np.arange(len(prs)))
    ax.set_xticklabels(prs)
    ax.set_xlabel('PR ID')
    ax.set_title('Baseline vs RAG Mean Score Heatmap')
    fig.colorbar(cax, label='Mean score')
    plt.tight_layout()
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png)
    plt.close()
    print("Heatmap saved to", out_png)


def parse_args():
    p = argparse.ArgumentParser(description="Plot RAG evaluation results")
    p.add_argument('--csv', '-c', default=str(CSV_PATH), help='Path to evaluation CSV')
    p.add_argument('--out-line', default=str(OUT_LINE_PNG), help='Path to save line chart PNG')
    p.add_argument('--out-heatmap', default=str(OUT_HEATMAP_PNG), help='Path to save heatmap PNG')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}. Run run_rag_evaluation.py first or pass --csv <path>.")

    plot_line_chart(str(csv_path), args.out_line)
    plot_heatmap(str(csv_path), args.out_heatmap)
