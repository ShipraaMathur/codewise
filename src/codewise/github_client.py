# src/codewise/github_client.py
from github import Github
import os

class GitHubClient:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("Missing GITHUB_TOKEN")
        self.client = Github(token)

    def get_pr(self, repo_name, pr_number: int):
        repo = self.client.get_repo(repo_name)
        return repo.get_pull(pr_number)

    def get_pr_files(self, repo_name, pr_number: int):
        pr = self.get_pr(repo_name, pr_number)
        files_data = []
        for f in pr.get_files():
            files_data.append({
                "filename": f.filename,
                "patch": f.patch or "",
                "status": f.status
            })
        return files_data

    def get_pr_review_comments(self, repo_name, pr_number: int):
        """
        Return a list of dicts with comments on the PR, matching what loaders.py expects.
        Each dict contains: 'body', 'path', 'position', 'user'.
        """
        pr = self.get_pr(repo_name, pr_number)
        comments = []
        for c in pr.get_review_comments():
            comments.append({
                "body": c.body,
                "path": c.path,
                "position": c.position,
                "user": c.user.login
            })
        return comments

    def get_diff(self, pr):
        diffs = []
        for file in pr.get_files():
            if file.patch:
                diffs.append(file.patch)
        return "\n".join(diffs)
