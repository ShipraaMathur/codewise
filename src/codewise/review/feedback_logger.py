import os
import json
import sqlite3
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
JSON_FILE = os.path.join(LOG_DIR, "feedback.json")
DB_FILE = os.path.join(LOG_DIR, "feedback.db")

class FeedbackLogger:
    def __init__(self):
        self.feedback = []
        self.conn = sqlite3.connect(DB_FILE)
        self._create_table()

    def _create_table(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pr_number TEXT,
                file_name TEXT,
                node_name TEXT,
                review TEXT,
                accepted BOOLEAN,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def add_feedback(self, pr_number, file_name, node_name, review_text):
        timestamp = datetime.utcnow().isoformat()
        # Add to in-memory JSON list
        self.feedback.append({
            "pr_number": pr_number,
            "file": file_name,
            "node": node_name,
            "review": review_text,
            "accepted": None,
            "timestamp": timestamp
        })
        # Add to SQLite
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO feedback (pr_number, file_name, node_name, review, accepted, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pr_number, file_name, node_name, review_text, None, timestamp))
        self.conn.commit()

    def save_json(self):
        with open(JSON_FILE, "w") as f:
            json.dump(self.feedback, f, indent=2)

    def update_feedback(self, pr_number, node_name, accepted: bool):
        # Update in SQLite
        c = self.conn.cursor()
        c.execute("""
            UPDATE feedback
            SET accepted = ?
            WHERE pr_number = ? AND node_name = ?
        """, (accepted, pr_number, node_name))
        self.conn.commit()
        # Update in-memory JSON
        for f in self.feedback:
            if f["pr_number"] == pr_number and f["node"] == node_name:
                f["accepted"] = accepted

    def compute_adaptation_params(self, pr_number=None):
        """
        Computes adaptation parameters like verbosity and tone based on past feedback.
        If pr_number is None, uses all feedback.
        """
        relevant_feedback = self.feedback
        if pr_number:
            relevant_feedback = [f for f in self.feedback if f["pr_number"] == pr_number]

        if not relevant_feedback:
            return {"verbosity": "medium", "tone": "neutral"}

        total = len(relevant_feedback)
        accepted_count = sum(1 for f in relevant_feedback if f["accepted"] is True)
        acceptance_rate = accepted_count / total if total else 0.5

        if acceptance_rate < 0.5:
            verbosity = "short"
            tone = "concise"
        elif acceptance_rate > 0.8:
            verbosity = "long"
            tone = "detailed"
        else:
            verbosity = "medium"
            tone = "neutral"

        return {"verbosity": verbosity, "tone": tone}    