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

    def get_diff(self, pr):
        diffs = []
        for file in pr.get_files():
            if file.patch:
                diffs.append(file.patch)
        return "\n".join(diffs)
