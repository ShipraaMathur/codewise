
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