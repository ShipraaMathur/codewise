import json
import os
import subprocess
import time
import sys
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

# Evaluation metrics (load per-PR metrics file if present)
try:
    with open("src/codewise/evaluation/evaluation_results/per_pr_metrics.json") as f:
        per_pr_metrics = json.load(f)
except FileNotFoundError:
    per_pr_metrics = None

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

# On-page PR input (empty by default) as a form so Enter submits
with st.form(key='pr_form'):
    st.markdown("### Load PR")
    pr_input = st.text_input("Enter PR number", key='pr_input')
    submitted = st.form_submit_button('Load PR')

if not submitted:
    st.stop()

# Parse PR number after user submits (Enter or button)
try:
    pr_number = int(pr_input)
except Exception:
    st.error("PR number must be an integer")
    st.stop()

st.write(f"**PR Number:** {pr_number}")
pr_title = rag_data.get("pr_title", "Unknown")
st.write(f"**PR Title:** {pr_title}")

# Filter AI feedback to the selected PR
filtered_ai = [entry for entry in ai_feedback if entry.get('pr_number') == int(pr_number)]

# Choose evaluation metrics for selected PR (from per_pr_metrics if available)
eval_metrics = None
if per_pr_metrics:
    for entry in per_pr_metrics:
        if entry.get('pr_id') == int(pr_number):
            eval_metrics = entry.get('metrics', {})
            break
if eval_metrics is None:
    # fallback to overall metrics.json
    try:
        with open("src/codewise/evaluation/evaluation_results/metrics.json") as f:
            overall = json.load(f)
            eval_metrics = {
                "rouge_l_avg": overall.get("rouge_l_avg", 0),
                "rouge_l_max": overall.get("rouge_l_max", 0),
                "rouge_l_min": overall.get("rouge_l_min", 0),
            }
    except FileNotFoundError:
        eval_metrics = {"rouge_l_avg": 0, "rouge_l_max": 0, "rouge_l_min": 0}

# Run the pipeline script to produce up-to-date data (github_test, retrieval_pipeline, evaluation)
pipeline_script = os.path.join('src', 'codewise', 'scripts', 'run_pr_pipeline.py')
if os.path.exists(pipeline_script):
    # Stream pipeline steps with live logs and progress
    def stream_command(cmd, start_pct, end_pct, title):
        """Run a command, suppress stdout in the UI, and move progress from start_pct to end_pct.

        This intentionally does not display the command output; it only shows a progress bar
        and a short completion status per step.
        """
        status_box = st.empty()
        status_box.info(f"{title} — running...")
        progress_bar = st.progress(start_pct)
        current = start_pct
        increment = max(1, (end_pct - start_pct) // 50)
        try:
            # suppress subprocess stdout/stderr from appearing in the Streamlit UI
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except Exception as e:
            status_box.error(f"Failed to start: {e}")
            progress_bar.progress(end_pct)
            return 1

        # Poll the process and advance the progress bar until it finishes
        while proc.poll() is None:
            current = min(current + increment, end_pct - 1)
            progress_bar.progress(int(current))
            time.sleep(0.15)

        rc = proc.returncode if proc.returncode is not None else proc.wait()
        # finish the step progress and show a small completion message
        progress_bar.progress(end_pct)
        if rc == 0:
            status_box.success(f"{title} — completed")
        else:
            status_box.error(f"{title} — exited with {rc}")
        return rc


    # Use the consolidated shell pipeline script instead of running individual steps
    steps = []
    cwd = os.getcwd()
    pipeline_sh = os.path.join(cwd, 'run_pipeline.sh')
    if os.path.exists(pipeline_sh):
        # run via bash to ensure the script executes regardless of executable bit
        steps.append(( ['/bin/bash', pipeline_sh, str(pr_number)], 1, 100, 'Running pipeline script (run_pipeline.sh)'))

    if steps:
        st.subheader('Running pipeline')
        overall_progress = st.progress(0)
        for cmd, start, end, title in steps:
            rc = stream_command(cmd, start, end, title)
            overall_progress.progress(end)
            # continue to next step even if rc != 0
    else:
        st.warning('No pipeline steps found; ensure scripts exist')
else:
    st.warning(f'Pipeline script not found at {pipeline_script}; skip auto-run')

# -------------------------------
# Evaluation Metrics
# -------------------------------
st.subheader("RAG Evaluation Metrics (ROUGE-L)")

# Check if ground truth is available
if eval_metrics.get('no_ground_truth'):
    st.warning(
        f"⚠️ Ground truth not available for this PR: {eval_metrics.get('reason', 'Unknown reason')}\n\n"
        f"**AI Comments Generated:** {eval_metrics.get('ai_total', 0)}\n\n"
        f"**Human Comments Available:** {eval_metrics.get('human_total', 0)}\n\n"
        "To enable evaluation:\n"
        "1. Add human comment ground-truth to `src/codewise/evaluation/ground_truth.json` for this PR, or\n"
        "2. Ensure the PR has code-review comments on GitHub (requires valid `GITHUB_TOKEN`)"
    )
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_val = eval_metrics.get('rouge_l_avg')
        st.metric("Average ROUGE-L", f"{avg_val:.4f}" if avg_val is not None else "N/A")
    with col2:
        max_val = eval_metrics.get('rouge_l_max')
        st.metric("Max ROUGE-L", f"{max_val:.4f}" if max_val is not None else "N/A")
    with col3:
        min_val = eval_metrics.get('rouge_l_min')
        st.metric("Min ROUGE-L", f"{min_val:.4f}" if min_val is not None else "N/A")
    
    st.write(f"**AI Comments:** {eval_metrics.get('ai_total', 0)} | **Human Comments:** {eval_metrics.get('human_total', 0)}")

# Severity Distribution
severity_counts = {}
for pr in filtered_ai:
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
files = list({pr['file'] for pr in filtered_ai})
if files:
    selected_file = st.selectbox("Select File", files)
    
    # Filter AI comments for selected file
    for pr in filtered_ai:
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

