import json
def extract_all_human_comments(pr):
    """
    Extracts all human comments from a PR:
      - Inline review comments
      - Top-level issue comments
      - Comments inside reviews
    Returns:
      dict: { PR_NUMBER: [ {path, line, body, severity} ] }
      int: number of comments
    """
    results = {str(pr.number): []}

    # 1. Inline review comments
    for c in pr.get_review_comments():
        results[str(pr.number)].append({
            "path": c.path,
            "line": c.position or c.original_position or 0,
            "body": c.body,
            "severity": "Low"
        })

    # 2. Top-level issue comments
    for c in pr.get_issue_comments():
        results[str(pr.number)].append({
            "path": None,
            "line": None,
            "body": c.body,
            "severity": "Low"
        })

    # 3. Comments inside reviews
    for review in pr.get_reviews():
        for c in review.get_comments():
            results[str(pr.number)].append({
                "path": c.path,
                "line": c.position or c.original_position or 0,
                "body": c.body,
                "severity": "Low"
            })

    return results, len(results[str(pr.number)])


def save_human_comments_to_json(pr, output_dir="output"):
    """
    Extracts human comments from the given PR and saves them to a JSON file.
    File path: output/human_comments_<PR_NUMBER>.json
    """
    import os
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    human_json, count = extract_all_human_comments(pr)
    file_path = os.path.join(output_dir, f"ground_truth.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(human_json, f, indent=4)

    print(f"Saved {count} human comments to {file_path}")

