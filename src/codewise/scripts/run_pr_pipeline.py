#!/usr/bin/env python3
"""
Run the full PR pipeline:
 - github_test.py
 - src/codewise/scripts/retrieval_pipeline.py
 - evaluation.run_eval

Usage:
  python run_pr_pipeline.py --pr 5853 [--owner-repo pallets/flask]
Or set env PR_NUMBER.
"""
import os
import sys
import argparse
import subprocess
from shutil import which

PY = sys.executable

def run_cmd(cmd, env=None):
    print(f"\n=== Running: {' '.join(cmd)} ===\n")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True)
    for line in proc.stdout:
        print(line, end="")
    proc.wait()
    return proc.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pr', type=int, help='PR number to run pipeline for')
    parser.add_argument('--owner-repo', default='pallets/flask', help='owner/repo string')
    parser.add_argument('--skip-github-test', action='store_true')
    parser.add_argument('--skip-retrieval', action='store_true')
    parser.add_argument('--skip-eval', action='store_true')
    args = parser.parse_args()

    pr = args.pr or os.environ.get('PR_NUMBER')
    if not pr:
        print('Error: PR number not provided. Use --pr or set PR_NUMBER env var.')
        sys.exit(2)
    pr = int(pr)
    owner_repo = args.owner_repo

    env = os.environ.copy()
    env['PR_NUMBER'] = str(pr)

    # Step 1: github_test.py (if present)
    if not args.skip_github_test:
        github_test = os.path.join(os.getcwd(), 'github_test.py')
        if os.path.exists(github_test):
            ret = run_cmd([PY, github_test, '--pr', str(pr)], env=env)
            if ret != 0:
                print(f'github_test.py exited with {ret}; continuing')
        else:
            print('github_test.py not found; skipping')

    # Step 2: retrieval pipeline
    if not args.skip_retrieval:
        retrieval = os.path.join(os.getcwd(), 'src', 'codewise', 'scripts', 'retrieval_pipeline.py')
        if os.path.exists(retrieval):
            ret = run_cmd([PY, retrieval, '--pr', str(pr)], env=env)
            if ret != 0:
                print(f'retrieval_pipeline.py exited with {ret}; continuing')
        else:
            print('retrieval_pipeline.py not found; skipping')

    # Step 3: evaluation
    if not args.skip_eval:
        # run as module
        ret = run_cmd([PY, '-m', 'src.codewise.evaluation.run_eval', '--prs', str(pr), '--owner-repo', owner_repo], env=env)
        if ret != 0:
            print(f'evaluation.run_eval exited with {ret}')

    print('\n=== Pipeline complete ===')

if __name__ == '__main__':
    main()
