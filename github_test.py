import os
from github import Github
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

if not token:
    raise ValueError("Missing GITHUB_TOKEN in .env!")

from github import Github, Auth

g = Github(auth=Auth.Token(token))

repo = g.get_repo("pallets/flask")   # Example repo

print("Connected to:", repo.full_name)

prs = repo.get_pulls(state="open")
print("\nOpen Pull Requests:")

for pr in prs[:5]:
    print(f"- #{pr.number}: {pr.title}")

    for file in pr.get_files():
        print("\nFile modified:", file.filename)
        print("Patch:\n", file.patch)
