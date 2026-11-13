"""
Authentication utilities and decorators for LabStock AI.
"""

from functools import wraps
from flask import session, redirect, url_for, request, jsonify


def login_required(f):
    """Decorator to require administrator login for view and API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/') or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "success": False,
                    "error": "Authentication required. Please log in as an administrator."
                }), 401
            return redirect(url_for('views.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
