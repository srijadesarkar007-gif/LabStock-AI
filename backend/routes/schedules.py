"""
Laboratory Practical Schedules Route Module for LabStock AI.

Handles viewing, listing, and resource readiness verification for scheduled
college engineering laboratory sessions.
"""

from flask import Blueprint, render_template, jsonify, request
from backend.db import get_db

schedules_bp = Blueprint('schedules', __name__)


@schedules_bp.route('/')
def list_schedules():
    """Render laboratory practical schedules and resource readiness dashboard."""
    conn = get_db()
    cursor = conn.cursor()

    # Query practical schedules with aggregated item requirement counts
    cursor.execute("""
        SELECT s.id, s.course_code, s.course_name, s.practical_title,
               s.lab_room, s.department, s.student_batch, s.student_count,
               s.scheduled_date, s.start_time, s.end_time, s.instructor_name, s.status,
               COUNT(r.item_id) as required_items_count
        FROM lab_schedules s
        LEFT JOIN schedule_requirements r ON s.id = r.schedule_id
        GROUP BY s.id
        ORDER BY s.scheduled_date ASC
    """)
    schedules = cursor.fetchall()

    # Fetch detailed requirements per schedule
    schedule_details = []
    for sched in schedules:
        cursor.execute("""
            SELECT r.required_quantity, i.name as item_name, i.item_code,
                   i.quantity as current_stock, i.unit,
                   CASE 
                       WHEN i.quantity >= r.required_quantity THEN 'Sufficient'
                       ELSE 'Deficit'
                   END as stock_readiness
            FROM schedule_requirements r
            JOIN items i ON r.item_id = i.id
            WHERE r.schedule_id = ?
        """, (sched['id'],))
        reqs = cursor.fetchall()
        
        has_deficit = any(r['stock_readiness'] == 'Deficit' for r in reqs)
        
        schedule_details.append({
            "schedule": sched,
            "requirements": reqs,
            "has_deficit": has_deficit
        })

    conn.close()
    return render_template('schedules.html', schedules=schedule_details)


@schedules_bp.route('/api', methods=['GET'])
def get_schedules_api():
    """Return schedules and resource readiness as JSON."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, COUNT(r.item_id) as items_needed
        FROM lab_schedules s
        LEFT JOIN schedule_requirements r ON s.id = r.schedule_id
        GROUP BY s.id
        ORDER BY s.scheduled_date ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    schedule_list = [dict(row) for row in rows]
    return jsonify({"schedules": schedule_list, "total": len(schedule_list)})
