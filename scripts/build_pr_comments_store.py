import os
from github import Github, Auth # type: ignore
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
if not token:
    raise ValueError("Missing GITHUB_TOKEN in .env!")

# Connect to GitHub
g = Github(auth=Auth.Token(token))
repo = g.get_repo("pallets/flask")
print("Connected to:", repo.full_name)

# ---------- Step 1: Fetch historical PR comments ----------
comments_data = []

print("Fetching PR review comments...")
for pr in repo.get_pulls(state="all")[:50]:
    for review_comment in pr.get_review_comments():
        if review_comment.body and review_comment.body.strip():
            comments_data.append({
                "text": review_comment.body,
                "type": "review_comment",
                "file": review_comment.path,
                "repo": repo.full_name
            })

print("Fetching issue comments (PR discussions)...")
for issue_comment in repo.get_issues_comments()[:50]:
    if '/pull/' in issue_comment.html_url and issue_comment.body and issue_comment.body.strip():
        comments_data.append({
            "text": issue_comment.body,
            "type": "issue_comment",
            "file": None,
            "repo": repo.full_name
        })

print(f"Total comments fetched: {len(comments_data)}")

# ---------- Step 2: Create embeddings ----------
emb = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(
    [c["text"] for c in comments_data],
    emb,
    metadatas=comments_data
)

# ---------- Step 3: Save vector store ----------
os.makedirs("vectorstores", exist_ok=True)
vectorstore.save_local("vectorstores/pr_comments_store")
print("PR comment embedding store saved at vectorstores/pr_comments_store")
