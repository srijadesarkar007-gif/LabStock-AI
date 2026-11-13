"""
REST API Endpoints for LabStock AI.

Includes KPI metrics, forecasting series, anomaly inspection, and Phase 3
interactive inventory operations (Add Item, Issue Stock with real-time AI anomaly detection,
and Restock).
"""

from flask import Blueprint, jsonify, request, session
from datetime import datetime
from backend.db import get_db
from backend.auth import login_required
from ai.forecasting import DemandForecaster
from ai.anomaly_detection import InventoryAnomalyDetector

api_bp = Blueprint('api', __name__)
forecaster = DemandForecaster()
anomaly_detector = InventoryAnomalyDetector()


# --------------------------------------------------------------------------
# Analytics & Reporting Endpoints
# --------------------------------------------------------------------------

@api_bp.route('/kpi', methods=['GET'])
def get_kpi_metrics():
    """Return key dashboard metrics as JSON."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM items")
    total_items = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE quantity <= minimum_threshold")
    low_stock = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantity * unit_cost) FROM items")
    valuation = cursor.fetchone()[0] or 0.0

    conn.close()
    return jsonify({
        "total_items": total_items,
        "low_stock_items": low_stock,
        "total_valuation_usd": round(valuation, 2),
        "status": "operational"
    })


@api_bp.route('/forecast/chart', methods=['GET'])
def get_forecast_chart_data():
    """Return time-series demand predictions for Chart.js."""
    conn = get_db()
    data = forecaster.generate_dashboard_forecast_series(conn)
    conn.close()
    return jsonify(data)


@api_bp.route('/forecast/item/<int:item_id>', methods=['GET'])
def get_item_forecast_api(item_id):
    """Return item-specific predictive metrics, safety stock, and reorder recommendation."""
    conn = get_db()
    data = forecaster.get_item_forecast(item_id, conn)
    conn.close()
    if not data:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(data)


@api_bp.route('/department-distribution', methods=['GET'])
def get_department_distribution():
    """Return inventory item counts grouped by department."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.department, COUNT(i.id) as item_count
        FROM categories c
        LEFT JOIN items i ON c.id = i.category_id
        GROUP BY c.department
    """)
    rows = cursor.fetchall()
    conn.close()

    labels = [row['department'] for row in rows]
    counts = [row['item_count'] for row in rows]

    return jsonify({
        "labels": labels,
        "counts": counts
    })


@api_bp.route('/anomalies', methods=['GET'])
def get_anomalies():
    """Return list of active flagged consumption anomalies from database."""
    conn = get_db()
    alerts = anomaly_detector.get_active_anomalies(conn)
    conn.close()
    return jsonify({"anomalies": alerts, "count": len(alerts)})


# --------------------------------------------------------------------------
# Phase 3 Interactive Operations: Add Item, Issue, Restock, Resolve
# --------------------------------------------------------------------------

@api_bp.route('/items', methods=['POST'])
@login_required
def add_item():
    """
    Register a new laboratory inventory item.
    Protected with administrator authentication.
    """
    data = request.get_json() or request.form
    if not data:
        return jsonify({"success": False, "error": "No input payload provided."}), 400

    # Required fields validation
    name = (data.get('name') or '').strip()
    item_code = (data.get('item_code') or '').strip().upper()
    category_id = data.get('category_id')
    lab_name = (data.get('lab_name') or '').strip()

    if not name or not item_code or not category_id or not lab_name:
        return jsonify({
            "success": False,
            "error": "Item Name, Item Code, Department/Category, and Lab Name are required."
        }), 400

    # Numeric fields validation
    try:
        quantity = int(data.get('quantity', 0))
        minimum_threshold = int(data.get('minimum_threshold', 10))
        unit_cost = float(data.get('unit_cost', 0.0))
        if quantity < 0 or minimum_threshold < 0 or unit_cost < 0:
            return jsonify({"success": False, "error": "Quantity, threshold, and cost must be non-negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid numeric value for quantity, threshold, or unit cost."}), 400

    unit = (data.get('unit') or 'units').strip()
    storage_location = (data.get('storage_location') or '').strip()
    batch_number = (data.get('batch_number') or '').strip() or None
    expiry_date = (data.get('expiry_date') or '').strip() or None
    supplier_id = data.get('supplier_id') or None

    # Validate expiry date format if provided
    if expiry_date:
        try:
            datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"success": False, "error": "Invalid expiry date format. Use YYYY-MM-DD."}), 400

    # Status determination
    if quantity == 0:
        status = 'Critical'
    elif quantity <= minimum_threshold:
        status = 'Low Stock'
    else:
        status = 'In Stock'

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check uniqueness of item_code
        cursor.execute("SELECT id FROM items WHERE item_code = ?", (item_code,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "error": f"Item code '{item_code}' already exists."}), 409

        # Insert new item
        cursor.execute("""
            INSERT INTO items 
            (item_code, name, category_id, supplier_id, lab_name, quantity, unit,
             minimum_threshold, unit_cost, storage_location, batch_number, expiry_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_code, name, category_id, supplier_id, lab_name, quantity, unit,
            minimum_threshold, unit_cost, storage_location, batch_number, expiry_date, status
        ))
        item_id = cursor.lastrowid

        # Log initial inventory transaction if quantity > 0
        if quantity > 0:
            cursor.execute("""
                INSERT INTO stock_transactions 
                (item_id, transaction_type, quantity, recipient_or_source, purpose, logged_by, notes)
                VALUES (?, 'RESTOCK', ?, 'Initial Inventory Setup', 'Opening Stock Inward', ?, 'Registered via Add Item')
            """, (item_id, quantity, session.get('full_name', 'Administrator')))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Item '{name}' ({item_code}) successfully added to inventory.",
            "item_id": item_id
        }), 201

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500


@api_bp.route('/items/<int:item_id>/issue', methods=['POST'])
@login_required
def issue_stock(item_id):
    """
    Issue laboratory component stock to students/batches.
    Decrements available stock, writes audit transaction, logs consumption,
    and runs real-time AI anomaly detection.
    """
    data = request.get_json() or request.form
    if not data:
        return jsonify({"success": False, "error": "No input payload provided."}), 400

    try:
        quantity_to_issue = int(data.get('quantity', 0))
        if quantity_to_issue <= 0:
            return jsonify({"success": False, "error": "Quantity to issue must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid issue quantity specified."}), 400

    issued_to = (data.get('issued_to') or '').strip()
    purpose = (data.get('purpose') or '').strip()

    if not issued_to or not purpose:
        return jsonify({"success": False, "error": "Student Batch / Recipient and Laboratory Purpose are required."}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check current stock with row locking in transaction
        cursor.execute("SELECT id, name, item_code, quantity, unit, minimum_threshold FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()

        if not item:
            conn.close()
            return jsonify({"success": False, "error": "Item not found."}), 404

        current_qty = item['quantity']
        if quantity_to_issue > current_qty:
            conn.close()
            return jsonify({
                "success": False,
                "error": f"Cannot issue {quantity_to_issue} {item['unit']}. Only {current_qty} currently available in stock."
            }), 400

        # Calculate new quantity and status
        new_qty = current_qty - quantity_to_issue
        if new_qty == 0:
            new_status = 'Critical'
        elif new_qty <= item['minimum_threshold']:
            new_status = 'Low Stock'
        else:
            new_status = 'In Stock'

        # Update item stock level
        cursor.execute("""
            UPDATE items 
            SET quantity = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_qty, new_status, item_id))

        # Record in stock audit transactions
        logged_by = session.get('full_name', 'Administrator')
        cursor.execute("""
            INSERT INTO stock_transactions 
            (item_id, transaction_type, quantity, recipient_or_source, purpose, logged_by)
            VALUES (?, 'ISSUE', ?, ?, ?, ?)
        """, (item_id, quantity_to_issue, issued_to, purpose, logged_by))

        # Record in consumption logs for time-series analytics
        today_str = datetime.now().date().isoformat()
        cursor.execute("""
            INSERT INTO consumption_logs 
            (item_id, quantity_used, logged_date, purpose, issued_to, is_anomaly)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (item_id, quantity_to_issue, today_str, purpose, issued_to))
        consumption_log_id = cursor.lastrowid

        # Trigger real-time AI anomaly detection
        anomaly_result = anomaly_detector.evaluate_and_log_anomaly(
            conn,
            item_id=item_id,
            consumption_log_id=consumption_log_id,
            quantity_issued=quantity_to_issue,
            issued_to=issued_to,
            purpose=purpose
        )

        conn.commit()
        conn.close()

        response_payload = {
            "success": True,
            "message": f"Issued {quantity_to_issue} {item['unit']} of '{item['name']}' to {issued_to}.",
            "new_quantity": new_qty,
            "status": new_status,
            "anomaly_detected": bool(anomaly_result)
        }
        if anomaly_result:
            response_payload["anomaly"] = anomaly_result

        return jsonify(response_payload), 200

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "error": f"Database transaction error: {str(e)}"}), 500


@api_bp.route('/items/<int:item_id>/restock', methods=['POST'])
@login_required
def restock_item(item_id):
    """
    Replenish stock for a laboratory component.
    Increases stock, updates batch number & expiry date if supplied,
    and logs an auditable RESTOCK transaction.
    """
    data = request.get_json() or request.form
    if not data:
        return jsonify({"success": False, "error": "No input payload provided."}), 400

    try:
        quantity_to_add = int(data.get('quantity', 0))
        if quantity_to_add <= 0:
            return jsonify({"success": False, "error": "Restock quantity must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid restock quantity."}), 400

    supplier_name = (data.get('supplier_name') or 'Supplier Delivery').strip()
    batch_number = (data.get('batch_number') or '').strip() or None
    expiry_date = (data.get('expiry_date') or '').strip() or None
    notes = (data.get('notes') or 'Periodic replenishment').strip()

    if expiry_date:
        try:
            datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"success": False, "error": "Invalid expiry date format. Use YYYY-MM-DD."}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name, quantity, unit, minimum_threshold, batch_number, expiry_date FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()

        if not item:
            conn.close()
            return jsonify({"success": False, "error": "Item not found."}), 404

        new_qty = item['quantity'] + quantity_to_add
        new_batch = batch_number if batch_number else item['batch_number']
        new_expiry = expiry_date if expiry_date else item['expiry_date']

        new_status = 'In Stock' if new_qty > item['minimum_threshold'] else 'Low Stock'

        cursor.execute("""
            UPDATE items 
            SET quantity = ?, status = ?, batch_number = ?, expiry_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_qty, new_status, new_batch, new_expiry, item_id))

        logged_by = session.get('full_name', 'Administrator')
        cursor.execute("""
            INSERT INTO stock_transactions 
            (item_id, transaction_type, quantity, recipient_or_source, purpose, logged_by, notes)
            VALUES (?, 'RESTOCK', ?, ?, 'Stock Replenishment', ?, ?)
        """, (item_id, quantity_to_add, supplier_name, logged_by, notes))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Successfully added {quantity_to_add} {item['unit']} to '{item['name']}'. New stock: {new_qty} {item['unit']}.",
            "new_quantity": new_qty,
            "status": new_status
        }), 200

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "error": f"Database transaction error: {str(e)}"}), 500


@api_bp.route('/anomalies/<int:anomaly_id>/resolve', methods=['POST'])
@login_required
def resolve_anomaly_api(anomaly_id):
    """Mark a flagged anomaly as reviewed/resolved by an administrator."""
    conn = get_db()
    success = anomaly_detector.resolve_anomaly(conn, anomaly_id)
    conn.commit()
    conn.close()

    if success:
        return jsonify({"success": True, "message": "Anomaly marked as resolved."}), 200
    else:
        return jsonify({"success": False, "error": "Anomaly record not found."}), 404
