# src/codewise/reviewer.py

from codewise.logger import get_logger
from codewise.review.llm_reviewer import get_review_for_code
from codewise.core.static_analyzer import analyze_file_changes

logger = get_logger(__name__)

class Reviewer:
    """
    Wrapper class for LLM-based code reviewer.
    Provides methods to:
      - generate_review(diff) : review a code snippet / diff
      - review_pr(repo, pr_number): review an entire GitHub PR
    """

    def __init__(self):
        logger.info("Reviewer initialized.")

    def generate_review(self, diff: str) -> list[str]:
        """
        Generate review comments for a PR diff or single code snippet.

        Args:
            diff (str): GitHub PR diff or code snippet.

        Returns:
            List of comment strings ready for CLI display.
        """
        if not diff.strip():
            logger.info("No diff provided, skipping review.")
            return ["No changes detected."]

        review_dict = get_review_for_code(diff)
        comments = []

        if review_dict and "review_comments" in review_dict:
            for c in review_dict["review_comments"]:
                line = c.get("line_number", -1)
                comment_text = c.get("comment", "")
                severity = c.get("severity", "Low")
                comments.append(f"[Line {line}] ({severity}) {comment_text}")
            logger.info(f"Generated {len(comments)} review comments.")
        else:
            comments.append("No issues detected by LLM reviewer.")
            logger.info("No issues detected by LLM reviewer.")

        return comments

    def review_pr(self, repo, pr_number, temperature=0.2) -> dict:
        """
        Generate a review for all Python files in a PR.
        Returns a structured dictionary similar to generatereview.py output.

        Args:
            repo: PyGithub repository object
            pr_number: PR number to review
            temperature: LLM temperature setting

        Returns:
            Dictionary containing reviews for all affected files.
        """
        full_review = {"pr_number": pr_number, "files": []}

        try:
            pr = repo.get_pull(pr_number)
            for file in pr.get_files():
                if not file.filename.endswith(".py"):
                    continue

                try:
                    file_content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode("utf-8")
                    patch_text = file.patch
                    affected_nodes = analyze_file_changes(file_content, patch_text)

                    file_review = {"filename": file.filename, "reviews": []}

                    for node_name, source_code in affected_nodes.items():
                        review = get_review_for_code(source_code, temperature=temperature)
                        if review:
                            file_review["reviews"].append({"node": node_name, "review": review})

                    if file_review["reviews"]:
                        full_review["files"].append(file_review)

                except Exception as e:
                    logger.exception(f"Could not analyze file {file.filename}: {e}")

            logger.info(f"Completed review for PR #{pr_number}")
            return full_review

        except Exception as e:
            logger.exception(f"Error reviewing PR #{pr_number}: {e}")
            return {"error": str(e)}
