"""
Anomaly Detection Module for LabStock AI.

Identifies unusual consumption spikes, unexpected bulk withdrawals, or potential
equipment hoarding/misplacement in college engineering laboratories.
Prepared for integration with Scikit-learn (IsolationForest, OneClassSVM) and NumPy.
"""

import sqlite3
from typing import List, Dict, Any, Optional


class InventoryAnomalyDetector:
    """Anomaly detection engine for engineering laboratory inventory."""

    def __init__(self, sensitivity: float = 2.0):
        # sensitivity corresponds to statistical standard deviation (Z-score threshold)
        self.sensitivity = sensitivity

    def detect_consumption_anomaly(self, current_usage: int, historical_usages: List[int]) -> Dict[str, Any]:
        """
        Evaluate if a single transaction or withdrawal qualifies as an anomaly.
        Uses statistical Z-score: Z = (x - mean) / std_dev.
        """
        if not historical_usages or len(historical_usages) < 3:
            # Baseline heuristic when history is limited:
            # Requisitioning > 15 units of sensitive lab gear in a single checkout is flagged
            is_anomaly = current_usage >= 15
            severity = "Critical" if current_usage >= 25 else "High" if is_anomaly else "Normal"
            return {
                "is_anomaly": is_anomaly,
                "z_score": 2.5 if is_anomaly else 0.5,
                "severity": severity,
                "reason": f"Bulk checkout of {current_usage} units exceeds normal laboratory batch baseline allocation." if is_anomaly else "Normal"
            }

        mean = sum(historical_usages) / len(historical_usages)
        variance = sum((x - mean) ** 2 for x in historical_usages) / len(historical_usages)
        std_dev = variance ** 0.5

        if std_dev == 0:
            std_dev = 1.0

        z_score = (current_usage - mean) / std_dev
        is_anomaly = z_score > self.sensitivity

        severity = "Normal"
        if is_anomaly:
            if z_score >= 3.5 or current_usage >= (mean * 3.5):
                severity = "Critical"
            elif z_score >= 2.5:
                severity = "High"
            else:
                severity = "Medium"

        return {
            "is_anomaly": is_anomaly,
            "z_score": round(z_score, 2),
            "severity": severity,
            "reason": (
                f"Consumption ({current_usage} units) is {round(z_score, 1)} standard deviations above rolling average ({round(mean, 1)} units)."
                if is_anomaly else "Normal"
            )
        }

    def evaluate_and_log_anomaly(
        self,
        conn: sqlite3.Connection,
        item_id: int,
        consumption_log_id: int,
        quantity_issued: int,
        issued_to: str,
        purpose: str
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate stock issue event against database history.
        If anomalous, automatically insert into anomaly_logs and update consumption_logs.
        """
        cursor = conn.cursor()

        # Query past consumption for this item
        cursor.execute(
            """SELECT quantity_used FROM consumption_logs 
               WHERE item_id = ? AND id != ?
               ORDER BY logged_date DESC LIMIT 50""",
            (item_id, consumption_log_id)
        )
        rows = cursor.fetchall()
        historical_usages = [r[0] for r in rows]

        eval_result = self.detect_consumption_anomaly(quantity_issued, historical_usages)

        if eval_result["is_anomaly"]:
            reason = f"Abnormal spike: {quantity_issued} units requisitioned by '{issued_to}' for '{purpose}'. {eval_result['reason']}"
            cursor.execute(
                """INSERT INTO anomaly_logs (item_id, consumption_log_id, severity, anomaly_reason, resolved)
                   VALUES (?, ?, ?, ?, 0)""",
                (item_id, consumption_log_id, eval_result["severity"], reason)
            )
            anomaly_id = cursor.lastrowid

            # Mark in consumption_logs
            cursor.execute(
                "UPDATE consumption_logs SET is_anomaly = 1 WHERE id = ?",
                (consumption_log_id,)
            )

            return {
                "id": anomaly_id,
                "is_anomaly": True,
                "severity": eval_result["severity"],
                "reason": reason,
                "z_score": eval_result["z_score"]
            }

        return None

    def get_active_anomalies(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Query active unresolved anomalies from database."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.severity, a.anomaly_reason, a.detected_at, a.resolved,
                   i.item_code, i.name as item_name, i.lab_name,
                   c.quantity_used, c.issued_to, c.purpose
            FROM anomaly_logs a
            JOIN items i ON a.item_id = i.id
            LEFT JOIN consumption_logs c ON a.consumption_log_id = c.id
            WHERE a.resolved = 0
            ORDER BY a.detected_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def resolve_anomaly(self, conn: sqlite3.Connection, anomaly_id: int) -> bool:
        """Mark an anomaly as reviewed/resolved."""
        cursor = conn.cursor()
        cursor.execute("UPDATE anomaly_logs SET resolved = 1 WHERE id = ?", (anomaly_id,))
        return cursor.rowcount > 0
