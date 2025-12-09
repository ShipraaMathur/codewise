# src/codewise/evaluation/run_eval.py
import argparse
from .evaluator import evaluate_many
from src.codewise.github_client import GitHubClient

import json
from dotenv import load_dotenv

load_dotenv()

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--prs", nargs="+", type=int, required=False, help="PR numbers to evaluate")
    p.add_argument("--from-file", type=str, help="file with PR numbers, one per line")
    p.add_argument("--owner-repo", default="pallets/flask")
    return p.parse_args()

def load_prs_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return [int(line.strip()) for line in f if line.strip()]

def main():
    args = parse_args()
    if args.from_file:
        prs = load_prs_from_file(args.from_file)
    elif args.prs:
        prs = args.prs
    else:
        raise SystemExit("Provide --prs or --from-file")

    # create your Github client (adjust constructor)
    gh = GitHubClient() 
    result = evaluate_many(prs, github_client=gh, owner_repo=args.owner_repo)
    print("Overall:", result["overall"])
    print("Saved to src/codewise/evaluation/evaluation_results/")
    # also print per-pr summary
    for pr in result["per_pr"]:
        print(f"PR {pr['pr_id']}: precision={pr['metrics']['precision']:.2f} recall={pr['metrics']['recall']:.2f} f1={pr['metrics']['f1']:.2f}")

if __name__ == "__main__":
    main()
