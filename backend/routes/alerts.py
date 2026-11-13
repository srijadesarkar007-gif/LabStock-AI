"""
Inventory Alerts Route Module for LabStock AI.

Handles critical inventory notifications:
- Low-stock warnings (below minimum safety threshold)
- Expiry date alerts (reagents and chemicals expiring within 30 days or expired)
- AI-flagged consumption anomaly notifications
"""

from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta
from backend.db import get_db

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('/')
def alerts_center():
    """Render unified inventory & lab safety alert center."""
    conn = get_db()
    cursor = conn.cursor()
    today_str = datetime.now().date().isoformat()
    thirty_days_later = (datetime.now().date() + timedelta(days=30)).isoformat()

    # 1. Low Stock Items
    cursor.execute("""
        SELECT i.id, i.item_code, i.name, i.lab_name, i.quantity, i.unit, 
               i.minimum_threshold, i.unit_cost, i.storage_location, i.status,
               c.name as category_name
        FROM items i
        JOIN categories c ON i.category_id = c.id
        WHERE i.quantity <= i.minimum_threshold
        ORDER BY i.quantity ASC
    """)
    low_stock_items = cursor.fetchall()

    # 2. Expired Items
    cursor.execute("""
        SELECT i.id, i.item_code, i.name, i.lab_name, i.quantity, i.unit, 
               i.batch_number, i.expiry_date, i.storage_location,
               c.name as category_name
        FROM items i
        JOIN categories c ON i.category_id = c.id
        WHERE i.expiry_date IS NOT NULL AND i.expiry_date < ?
        ORDER BY i.expiry_date ASC
    """, (today_str,))
    expired_items = cursor.fetchall()

    # 3. Expiring Soon Items (within 30 days)
    cursor.execute("""
        SELECT i.id, i.item_code, i.name, i.lab_name, i.quantity, i.unit, 
               i.batch_number, i.expiry_date, i.storage_location,
               c.name as category_name
        FROM items i
        JOIN categories c ON i.category_id = c.id
        WHERE i.expiry_date IS NOT NULL 
          AND i.expiry_date >= ? 
          AND i.expiry_date <= ?
        ORDER BY i.expiry_date ASC
    """, (today_str, thirty_days_later))
    expiring_soon_items = cursor.fetchall()

    # 4. Active Anomaly Logs
    cursor.execute("""
        SELECT a.id, a.severity, a.anomaly_reason, a.detected_at, a.resolved,
               i.item_code, i.name as item_name, i.lab_name
        FROM anomaly_logs a
        JOIN items i ON a.item_id = i.id
        WHERE a.resolved = 0
        ORDER BY a.detected_at DESC
    """)
    active_anomalies = cursor.fetchall()

    conn.close()

    counts = {
        "low_stock": len(low_stock_items),
        "expired": len(expired_items),
        "expiring_soon": len(expiring_soon_items),
        "anomalies": len(active_anomalies),
        "total_critical": len(low_stock_items) + len(expired_items) + len(active_anomalies)
    }

    return render_template(
        'alerts.html',
        counts=counts,
        low_stock_items=low_stock_items,
        expired_items=expired_items,
        expiring_soon_items=expiring_soon_items,
        anomalies=active_anomalies
    )


@alerts_bp.route('/api/summary', methods=['GET'])
def get_alerts_summary():
    """Return counts of active inventory and expiry alerts for status badges."""
    conn = get_db()
    cursor = conn.cursor()
    today_str = datetime.now().date().isoformat()
    thirty_days_later = (datetime.now().date() + timedelta(days=30)).isoformat()

    cursor.execute("SELECT COUNT(*) FROM items WHERE quantity <= minimum_threshold")
    low_stock = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE expiry_date IS NOT NULL AND expiry_date < ?", (today_str,))
    expired = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE expiry_date IS NOT NULL AND expiry_date >= ? AND expiry_date <= ?", (today_str, thirty_days_later))
    expiring_soon = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM anomaly_logs WHERE resolved = 0")
    anomalies = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "low_stock_count": low_stock,
        "expired_count": expired,
        "expiring_soon_count": expiring_soon,
        "anomaly_count": anomalies,
        "total_action_required": low_stock + expired + expiring_soon + anomalies
    })
