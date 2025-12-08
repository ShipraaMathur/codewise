import argparse
from codewise.logger import get_logger
from codewise.github_client import GitHubClient
from codewise.reviewer import Reviewer
from dotenv import load_dotenv

load_dotenv()

logger = get_logger()

def run_review(repo: str, pr_number: int):
    logger.info(f"Starting review for {repo} PR #{pr_number}")

    try:
        gh = GitHubClient()
        pr = gh.get_pr(repo, pr_number)

        diff = gh.get_diff(pr)
        logger.info("Successfully extracted diff")

        reviewer = Reviewer()
        comments = reviewer.generate_review(diff)

        print("\n===== AI REVIEW COMMENTS =====\n")
        for c in comments:
            print("-", c)

        logger.info("Review generation completed successfully")

    except Exception as e:
        logger.exception("Error in running review")

def main():
    parser = argparse.ArgumentParser(description="CodeWise CLI")

    sub = parser.add_subparsers(dest="command")

    # review command
    review_cmd = sub.add_parser("review")
    review_cmd.add_argument("--repo", required=True, help="Repo like pallets/flask")
    review_cmd.add_argument("--pr", required=True, type=int)

    args = parser.parse_args()

    if args.command == "review":
        run_review(args.repo, args.pr)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
