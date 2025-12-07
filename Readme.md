
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

