import json
import pandas as pd
import streamlit as st

# -------------------------------
# Load Data
# -------------------------------
# AI feedback from CodeWise reviews
try:
    with open("src/logs/feedback.json") as f:
        ai_feedback = json.load(f)
except FileNotFoundError:
    st.error("AI feedback file not found: src/logs/feedback.json")
    ai_feedback = []

# Evaluation metrics
try:
    with open("src/codewise/evaluation/evaluation_results/per_pr_metrics.json") as f:
        per_pr_metrics = json.load(f)
        # Get the first PR's metrics (or find the matching PR if available)
        if per_pr_metrics:
            eval_metrics = per_pr_metrics[0]["metrics"]
        else:
            eval_metrics = {"rouge_l_avg": 0, "rouge_l_max": 0, "rouge_l_min": 0}
except FileNotFoundError:
    st.warning("Evaluation metrics not found")
    eval_metrics = {"rouge_l_avg": 0, "rouge_l_max": 0, "rouge_l_min": 0}

# RAG retrieval context
try:
    with open("pr_retrieval_output.json") as f:
        rag_data = json.load(f)
except FileNotFoundError:
    st.warning("RAG retrieval output not found")
    rag_data = {}

# -------------------------------
# Dashboard Header
# -------------------------------
st.title("CodeWise PR Dashboard")
st.subheader("Pull Request Summary")

# On-page PR input (empty by default)
st.markdown("### Load PR")
pr_input = st.text_input("Enter PR number")
load_pr = st.button("Load PR")

# If no PR entered yet, keep page empty until user loads a PR
if not pr_input or not load_pr:
    st.stop()

# Parse PR number after user submits
try:
    pr_number = int(pr_input)
except ValueError:
    st.error("PR number must be an integer")
    st.stop()

st.write(f"**PR Number:** {pr_number}")
pr_title = rag_data.get("pr_title", "Unknown")
st.write(f"**PR Title:** {pr_title}")

# Filter AI feedback to the selected PR
filtered_ai = [entry for entry in ai_feedback if entry.get('pr_number') == int(pr_number)]

# -------------------------------
# Evaluation Metrics
# -------------------------------
st.subheader("RAG Evaluation Metrics (ROUGE-L)")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average ROUGE-L", f"{eval_metrics.get('rouge_l_avg', 0):.4f}")
with col2:
    st.metric("Max ROUGE-L", f"{eval_metrics.get('rouge_l_max', 0):.4f}")
with col3:
    st.metric("Min ROUGE-L", f"{eval_metrics.get('rouge_l_min', 0):.4f}")

# Severity Distribution
severity_counts = {}
for pr in ai_feedback:
    review_data = json.loads(pr["review"])
    for comment in review_data.get("review_comments", []):
        sev = comment.get("severity", "Unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

if severity_counts:
    st.subheader("AI Comment Severity Distribution")
    severity_df = pd.DataFrame(list(severity_counts.items()), columns=["Severity", "Count"])
    st.bar_chart(severity_df.set_index("Severity"))

# -------------------------------
# File Diffs and AI Comments
# -------------------------------
st.subheader("File Diffs and AI Comments")
files = list(set([pr['file'] for pr in ai_feedback]))
if files:
    selected_file = st.selectbox("Select File", files)
    
    # Filter AI comments for selected file
    for pr in ai_feedback:
        if pr['file'] == selected_file:
            review_data = json.loads(pr["review"])
            for comment in review_data.get("review_comments", []):
                st.markdown(
                    f"**Line {comment['line_number']}**: {comment['comment']} "
                    f"(Severity: {comment['severity']})"
                )

    # RAG retrieved context
    st.subheader("Top Retrieved Context (RAG)")
    for file_data in rag_data.get("files", []):
        if file_data["filename"] == selected_file:
            for node in file_data.get("nodes", []):
                st.markdown(f"### Node: {node['node_name']}")
                
                # Top Code Matches
                for i, code_match in enumerate(node.get("top_code_matches", []), 1):
                    st.markdown(f"**Code Match {i}:**")
                    st.code(code_match["content"][:500] + "...", language="python")
                
                # Top PR Comments
                for i, comment_match in enumerate(node.get("top_pr_comments", []), 1):
                    snippet = comment_match["content"][:300] + "..."
                    st.markdown(f"**Comment {i}:** {snippet}")
else:
    st.info("No files with AI comments found for this PR.")

# -------------------------------
# Footer
# -------------------------------
st.markdown("---")

