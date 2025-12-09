
##  Setup Instructions

### **1. Clone the Repository**

```bash
git clone https://github.com/<your-username>/codewise.git
cd codewise

python3 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# OR
.venv\Scripts\activate          # Windows

pip install -r requirements.txt

```

Test Github connection:

```
python github_test.py

```

Build code embeddings
```
python scripts/build_vectorstore.py
```

Build PR comment embeddings
```
python scripts/build_pr_comments_store.py
```

Run the retrieval pipeline for a given PR
```
python scripts/retrieval_pipeline.py
```

Test PR diff extraction and LLM review generation:

```
python github_test.py

```
Test Temparature variants and Visualize the results:

```
python tests/test_temperature_variants.py --pr-url {PR_URL}

python tests/visualize_results.py tests/{CSV_File}

```

Test Rag Pipeline Promptchain Integration

```
python .\src\codewise\review\generate_review.py --pr-url https://github.com/pallets/flask/pull/5121

```
Test Adjust future review tone/verbosity based on feedback
 
```
python src/codewise/review/test_adaptation.py

```

To get evaluation

```
python -m src.codewise.evaluation.run_eval --prs 5121 --owner-repo pallets/flask

```