import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from codewise.review.feedback_logger import FeedbackLogger
from codewise.review.llm_reviewer import get_review_for_code
# Add the project root to the Python path to allow imports from 'src'

# ----------------------------
# 1️⃣ Simulate past feedback
# ----------------------------
logger = FeedbackLogger()

# Manually populate some feedback (simulate most rejected comments)
logger.feedback = [
    {"pr_number": "123", "file": "example.py", "node": "add_numbers", "review": "Use better variable names", "accepted": False, "timestamp": "2025-12-09T00:00:00"},
    {"pr_number": "123", "file": "example.py", "node": "add_numbers", "review": "Add type hints", "accepted": False, "timestamp": "2025-12-09T00:01:00"},
]

# Compute adaptation parameters
adaptation_params = logger.compute_adaptation_params(pr_number="123")
print("Adaptation parameters:", adaptation_params)

# ----------------------------
# 2️⃣ Test LLM review generation
# ----------------------------
sample_code = """
def add_numbers(a, b):
    result = a + b
    return result
"""

review = get_review_for_code(
    source_code=sample_code,
    retrieved_context="",  # empty for simulation
    temperature=0.2,
    adaptation_params=adaptation_params
)

print("\nGenerated review:")
print(review)

# ----------------------------
# 3️⃣ Optional: Save simulated feedback
# ----------------------------
logger.add_feedback(pr_number="123", file_name="example.py", node_name="add_numbers", review_text=str(review))
logger.save_json()
print("\nFeedback saved to logs/feedback.json")
