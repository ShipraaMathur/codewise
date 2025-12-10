#!/bin/bash
set -e  # stop on first error

# -------------------------------
# Activate environment (optional)
# -------------------------------
# Uncomment if you want:
# source activate codewise-faiss
# or:
# source .venv/bin/activate

PR_NUMBER="$1"

if [ -z "$PR_NUMBER" ]; then
  echo "❌ Error: No PR number provided."
  echo "Usage: ./pipeline.sh 5853"
  exit 1
fi

echo "🚀 Running full pipeline for PR #$PR_NUMBER"
echo "-----------------------------------------"

# 1️⃣ github_test.py
echo "▶️  Step 1: github_test.py"
python github_test.py --pr "$PR_NUMBER"

# 2️⃣ Build vector store
echo "▶️  Step 2: build_vectorstore.py"
python src/codewise/scripts/build_vectorstore.py

# 3️⃣ Build PR comments store
echo "▶️  Step 3: build_pr_comments_store.py"
python src/codewise/scripts/build_pr_comments_store.py

# 4️⃣ Retrieval pipeline
echo "▶️  Step 4: retrieval_pipeline.py"
python src/codewise/scripts/retrieval_pipeline.py --pr "$PR_NUMBER"

# 5️⃣ Generate review (your AI-generated comments)
echo "▶️  Step 5: generate_review.py"
python src/codewise/review/generate_review.py --pr-url https://github.com/pallets/flask/pull/"$PR_NUMBER"

# python .\src\codewise\review\generate_review.py --pr-url https://github.com/pallets/flask/pull/5853
# 6️⃣ Evaluation
echo "▶️  Step 6: evaluation.run_eval"
python -m src.codewise.evaluation.run_eval \
    --prs "$PR_NUMBER" \
    --owner-repo "pallets/flask"

echo ""
echo "✅ Pipeline complete for PR #$PR_NUMBER"
