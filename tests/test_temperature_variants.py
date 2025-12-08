import argparse
import subprocess
import time
import csv
import json
import re
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE other imports
load_dotenv()
def run_generation(pr_url, temperature):
    """Runs the review generation script and returns the output."""
    command = [
        "python",
        "src/review/generate_review.py",
        "--pr-url",
        pr_url,
        "--temperature",
        str(temperature)
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running generation for temperature {temperature}:")
        print(e.stderr)
        return None

def count_review_comments(review_json_str: str) -> int:
    """Parses the review JSON and counts the total number of review comments."""
    if not review_json_str:
        return 0
    try:
        review_data = json.loads(review_json_str)
        comment_count = 0
        for file_review in review_data.get("files", []):
            for node_review in file_review.get("reviews", []):
                comment_count += len(node_review.get("review", {}).get("review_comments", []))
        return comment_count
    except json.JSONDecodeError:
        return 0

def main():
    # Generate a default filename with a timestamp to avoid overwriting previous results.
    default_filename = f"temperature_test_results_{int(time.time())}.csv"

    parser = argparse.ArgumentParser(description="Test different temperature settings for review generation.")
    parser.add_argument("--pr-url", required=True, help="The URL of the pull request to test.")
    parser.add_argument("--output-file", default=default_filename, help=f"The CSV file to save results to (default: {default_filename}).")
    args = parser.parse_args()

    temperatures_to_test = [0.0, 0.2, 0.5, 0.8, 1.0]
    results = []

    for i, temp in enumerate(temperatures_to_test):
        print(f"--- Testing temperature: {temp} ---")
        start_time = time.time()
        generated_review = run_generation(args.pr_url, temp)
        end_time = time.time()

        if generated_review:
            duration = end_time - start_time
            review_length = len(generated_review)
            # Parse the JSON and count the number of review comments.
            num_review_comments = count_review_comments(generated_review)

            metrics = {
                "temperature": temp,
                "duration_seconds": round(duration, 2),
                "review_length_chars": review_length,
                "num_review_comments": num_review_comments,
                "generated_review": generated_review.strip()
            }
            results.append(metrics)
            print(f"Finished in {metrics['duration_seconds']}s. Found {metrics['num_review_comments']} review comments.")

        # Add a delay between tests to avoid hitting API rate limits, but skip after the last one.
        if i < len(temperatures_to_test) - 1:
            print("--- Waiting for 20 seconds to avoid rate limits... ---")
            time.sleep(20)

    # Handle case where no results were generated
    if not results:
        print("\n❌ Testing failed. No results were generated. Please check the errors from the generation script above.")
        return

    # Write results to CSV
    with open(args.output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = results[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Testing complete. Results saved to {args.output_file}")

if __name__ == "__main__":
    main()