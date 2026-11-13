"""
Synthetic / Simulated consumption data generator for LabStock AI.
Generates simulated semester-based consumption patterns for machine learning benchmarking:
- Simulated regular weekly academic lab practical sessions
- Simulated mid-term and end-semester project surges
- Simulated hackathon workshops
- Simulated anomalous checkout spikes for AI detection testing
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'labstock.db')


def generate_semester_history(db_path=DB_PATH, days_back=120):
    """Populate database with 4 months of realistic college lab usage logs."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get items
    cursor.execute("SELECT id, item_code, name, lab_name FROM items")
    items = cursor.fetchall()
    if not items:
        print("No items found. Run init_db.py first.")
        conn.close()
        return

    # Check if we already have deep history
    cursor.execute("SELECT COUNT(*) FROM consumption_logs")
    count = cursor.fetchone()[0]
    if count > 20:
        print(f"Historical consumption logs already exist ({count} entries).")
        conn.close()
        return

    print(f"Generating {days_back} days of realistic academic lab history...")

    batches = [
        "ECE 3rd Year - Batch A", "ECE 3rd Year - Batch B",
        "CSE/IoT 2nd Year - Sec 1", "CSE/IoT 2nd Year - Sec 2",
        "Mechanical 4th Year - Capstone", "Robotics Club Project Team",
        "Electrical 3rd Year - Power Lab", "Chemistry Core Practicals"
    ]

    purposes = [
        "Weekly Scheduled Laboratory Session",
        "Mini Project Prototyping",
        "Semester End Practical Examination",
        "Autonomous Robotics Competition Prep",
        "Student Research Work",
        "Lab Equipment Maintenance"
    ]

    today = datetime.now().date()
    logs_to_insert = []
    anomalies_to_insert = []

    # Daily simulation over past days_back days
    for day_offset in range(days_back, 0, -1):
        current_date = today - timedelta(days=day_offset)
        weekday = current_date.weekday()

        # College labs are usually active Monday-Friday (0-4), minimal on weekends
        if weekday >= 5 and random.random() > 0.15:
            continue

        # Simulating semester peaks: mid-semester (days 50-70 back) and end-sem (days 10-25 back)
        is_exam_peak = (50 <= day_offset <= 70) or (10 <= day_offset <= 25)
        activity_multiplier = 1.8 if is_exam_peak else 1.0

        for item in items:
            item_id = item['id']
            # Probability of an item being requisitioned on any given lab day
            prob = 0.35 if "Sensor" in item['name'] or "Resistor" in item['name'] or "Filament" in item['name'] else 0.20
            if random.random() < (prob * activity_multiplier):
                base_qty = random.randint(1, 5)

                # Inject deliberate anomalies periodically (about 3-4% chance)
                is_anomaly = False
                if random.random() < 0.035:
                    is_anomaly = True
                    base_qty = random.randint(14, 25) # Major abnormal checkout

                logs_to_insert.append((
                    item_id,
                    base_qty,
                    str(current_date),
                    "Semester Practical Peak" if is_exam_peak else random.choice(purposes),
                    random.choice(batches),
                    1 if is_anomaly else 0
                ))

    # Insert consumption logs
    cursor.executemany(
        """INSERT INTO consumption_logs 
           (item_id, quantity_used, logged_date, purpose, issued_to, is_anomaly)
           VALUES (?, ?, ?, ?, ?, ?)""",
        logs_to_insert
    )

    # Link anomalies to anomaly_logs table
    cursor.execute("""
        SELECT id, item_id, quantity_used, logged_date, issued_to 
        FROM consumption_logs 
        WHERE is_anomaly = 1
    """)
    anomaly_records = cursor.fetchall()

    for rec in anomaly_records:
        cursor.execute("SELECT name FROM items WHERE id = ?", (rec['item_id'],))
        item_row = cursor.fetchone()
        item_name = item_row['name'] if item_row else "Lab Item"

        reason = f"Abnormal spike: {rec['quantity_used']} units requisitioned by {rec['issued_to']} (exceeds regular lab batch quota)."
        severity = "Critical" if rec['quantity_used'] >= 20 else "High"

        cursor.execute("""
            INSERT INTO anomaly_logs (item_id, consumption_log_id, severity, anomaly_reason, resolved)
            VALUES (?, ?, ?, ?, 0)
        """, (rec['item_id'], rec['id'], severity, reason))

    conn.commit()
    conn.close()
    print(f"Successfully generated {len(logs_to_insert)} lab consumption events with {len(anomaly_records)} anomaly cases.")


if __name__ == '__main__':
    generate_semester_history()
