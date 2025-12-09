from github import GithubException

def post_comments_to_github(pr, comments):
    """
    comments = [
        {
            "text": "...",
            "file_path": "src/app.py",
            "line_number": 42
        }
    ]
    """
    for c in comments:
        if not c["line_number"]:
            continue  # skip if no line to anchor

        try:
            pr.create_review_comment(
                body=c["text"],
                commit_id=pr.head.sha,
                path=c["file_path"],
                line=c["line_number"],
            )
            print(f"Posted comment on {c['file_path']}:{c['line_number']}")
        except GithubException as e:
            print(f"Failed to post comment: {e}")
