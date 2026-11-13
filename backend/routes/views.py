from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from backend.db import get_db
from backend.auth import login_required
from ai.forecasting import DemandForecaster
from ai.anomaly_detection import InventoryAnomalyDetector

views_bp = Blueprint('views', __name__)
forecaster = DemandForecaster()
anomaly_detector = InventoryAnomalyDetector()


@views_bp.route('/')
def dashboard():
    """Render the primary academic dashboard overview."""
    conn = get_db()
    cursor = conn.cursor()
    today_str = datetime.now().date().isoformat()
    thirty_days_later = (datetime.now().date() + timedelta(days=30)).isoformat()

    # KPI Summary Queries
    cursor.execute("SELECT COUNT(*) FROM items")
    total_items = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE quantity <= minimum_threshold")
    low_stock_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT lab_name) FROM items")
    active_labs_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM anomaly_logs WHERE resolved = 0")
    pending_anomalies = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM items 
        WHERE expiry_date IS NOT NULL AND expiry_date <= ?
    """, (thirty_days_later,))
    expiring_count = cursor.fetchone()[0]

    # Recent Low Stock / Alert Items
    cursor.execute("""
        SELECT i.item_code, i.name, i.lab_name, i.quantity, i.unit, i.minimum_threshold, i.status, c.name as category_name
        FROM items i
        JOIN categories c ON i.category_id = c.id
        ORDER BY (i.quantity <= i.minimum_threshold) DESC, i.id ASC
        LIMIT 6
    """)
    recent_items = cursor.fetchall()

    # Calculate genuine model evaluation fit (R^2 score) from database series
    forecast_info = forecaster.generate_dashboard_forecast_series(conn)
    r_squared_pct = forecast_info.get('r_squared_pct', 85.0)

    conn.close()

    kpi_data = {
        "total_items": total_items,
        "low_stock_count": low_stock_count,
        "active_labs_count": active_labs_count,
        "pending_anomalies": pending_anomalies,
        "expiring_count": expiring_count,
        "model_r2_score": f"{r_squared_pct}%",
        "r_squared_raw": forecast_info.get('r_squared', 0.85)
    }

    return render_template('index.html', kpi=kpi_data, items=recent_items)


@views_bp.route('/inventory')
def inventory():
    """Render the full laboratory inventory page."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.item_code, i.name, i.lab_name, i.quantity, i.unit, 
               i.minimum_threshold, i.unit_cost, i.storage_location, i.status, 
               i.batch_number, i.expiry_date, i.category_id, i.supplier_id,
               c.name as category_name, c.department,
               s.name as supplier_name
        FROM items i
        JOIN categories c ON i.category_id = c.id
        LEFT JOIN suppliers s ON i.supplier_id = s.id
        ORDER BY i.id ASC
    """)
    items = cursor.fetchall()

    cursor.execute("SELECT id, name, department FROM categories ORDER BY name ASC")
    categories = cursor.fetchall()

    cursor.execute("SELECT id, name FROM suppliers ORDER BY name ASC")
    suppliers = cursor.fetchall()

    conn.close()
    return render_template('inventory.html', items=items, categories=categories, suppliers=suppliers)


@views_bp.route('/analytics')
def analytics():
    """Render AI predictive forecasting and anomaly detection center."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, a.severity, a.anomaly_reason, a.detected_at, a.resolved,
               i.item_code, i.name as item_name, i.lab_name,
               c.quantity_used as quantity_logged, c.purpose, c.issued_to
        FROM anomaly_logs a
        JOIN items i ON a.item_id = i.id
        LEFT JOIN consumption_logs c ON a.consumption_log_id = c.id
        WHERE a.resolved = 0
        ORDER BY a.detected_at DESC
    """)
    anomalies = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM anomaly_logs WHERE resolved = 0")
    active_anomalies_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM anomaly_logs WHERE resolved = 1")
    resolved_anomalies_count = cursor.fetchone()[0]

    forecast_info = forecaster.generate_dashboard_forecast_series(conn)

    cursor.execute("SELECT id, item_code, name, lab_name, quantity, unit FROM items ORDER BY name ASC")
    items = cursor.fetchall()

    conn.close()
    return render_template(
        'analytics.html',
        anomalies=anomalies,
        active_anomalies_count=active_anomalies_count,
        resolved_anomalies_count=resolved_anomalies_count,
        forecast=forecast_info,
        items=items
    )

@views_bp.route('/consumption')
def consumption():
    """Display actual laboratory consumption history."""
    conn = get_db()
    cursor = conn.cursor()

    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'all')
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    conditions = []
    params = []

    if search:
        conditions.append(
            "(i.name LIKE ? OR i.item_code LIKE ? OR "
            "c.issued_to LIKE ? OR c.purpose LIKE ?)"
        )
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if status == 'flagged':
        conditions.append("c.is_anomaly = 1")
    elif status == 'normal':
        conditions.append("c.is_anomaly = 0")

    if start_date:
        conditions.append("c.logged_date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("c.logged_date <= ?")
        params.append(end_date)

    where_clause = (
        "WHERE " + " AND ".join(conditions) if conditions else ""
    )

    cursor.execute(f"""
        SELECT c.id, c.logged_date, c.created_at,
               c.quantity_used, c.purpose, c.issued_to,
               c.is_anomaly, i.item_code, i.name AS item_name,
               i.lab_name, i.unit
        FROM consumption_logs c
        JOIN items i ON c.item_id = i.id
        {where_clause}
        ORDER BY c.logged_date DESC, c.created_at DESC
    """, params)

    logs = cursor.fetchall()

    cursor.execute(f"""
        SELECT COUNT(*) AS total_records,
               COALESCE(SUM(c.quantity_used), 0) AS total_quantity
        FROM consumption_logs c
        JOIN items i ON c.item_id = i.id
        {where_clause}
    """, params)

    summary = cursor.fetchone()

    conn.close()

    return render_template(
        'consumption.html',
        logs=logs,
        summary=summary,
        search=search,
        status=status,
        start_date=start_date,
        end_date=end_date
    )


@views_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Administrator / faculty authentication portal."""
    if 'user_id' in session and request.method == 'GET':
        return redirect(url_for('views.dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            next_url = request.args.get('next') or url_for('views.dashboard')
            return redirect(next_url)
        else:
            error = "Invalid administrator credentials. Please check your username and password."

    return render_template('login.html', error=error)


@views_bp.route('/logout')
def logout():
    """Clear administrator session and redirect to login."""
    session.clear()
    return redirect(url_for('views.login'))

