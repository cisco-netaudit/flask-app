"""
This module defines route handlers for logging, theming, profile updates,
report management, and redirection in a Flask application.
"""

from flask import current_app, jsonify, request, session, redirect, url_for, Response, send_from_directory, abort, make_response
import json
import os
import tempfile
import bcrypt
from datetime import datetime


def activity():
    """
    Streams application logs in real-time.

    Yields:
        str: Log entries formatted for server-sent events (SSE).
    """
    log_queue = current_app.logger.get_queue()
    history = current_app.logger.get_history()

    def event_stream():
        for log_entry in history:
            yield f"data: {json.dumps(log_entry)}\n\n"

        while True:
            log_entry = log_queue.get()
            yield f"data: {json.dumps(log_entry)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")

def set_theme():
    """
    Updates the theme for the currently logged-in user.
    """
    username = session.get("username")
    if not username:
        return jsonify(success=False, message="No user logged in"), 401

    theme_data = request.get_json()

    user_data = current_app.users_db.get(username, {})
    user_data.update(theme_data)
    current_app.users_db.update({username: user_data})

    session["theme"] = theme_data.get("theme", session.get("theme", "light"))

    return jsonify(success=True)


def update_profile():
    """
    Updates the profile information for the currently logged-in user.
    """
    username = session.get("username")
    if not username:
        return jsonify(success=False, message="No user logged in"), 401

    user_data = current_app.users_db.get(username, {})

    user_data["firstname"] = request.form.get("firstname", user_data.get("firstname"))
    user_data["lastname"] = request.form.get("lastname", user_data.get("lastname"))
    user_data["email"] = request.form.get("email", user_data.get("email"))

    password = request.form.get("password")
    if password:
        user_data["password"] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    current_app.users_db.update({username: user_data})

    return jsonify(success=True)


def get_reports():
    """
    Returns a list of report files from the user's reports directory.
    """
    reports_dir = session.get("reports_dir")
    if not reports_dir or not os.path.exists(reports_dir):
        return jsonify([])

    files = []
    for f in os.listdir(reports_dir):
        path = os.path.join(reports_dir, f)
        if os.path.isfile(path):
            created = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
            files.append({
                "filename": f,
                "created": created
            })

    # Sort by most recent first
    files.sort(key=lambda x: x["created"], reverse=True)
    return jsonify(files)


def download_report(filename):
    """
    Sends a specific report file for download.
    """
    reports_dir = session.get("reports_dir")
    if not reports_dir or not os.path.exists(reports_dir):
        abort(404)
    try:
        return send_from_directory(reports_dir, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

def delete_report(filename):
    """
    Deletes a specific report file from the user's reports directory.
    """
    reports_dir = session.get("reports_dir")
    if not reports_dir or not os.path.exists(reports_dir):
        return jsonify(success=False, message="Reports directory not found"), 404

    filepath = os.path.join(reports_dir, filename)

    # Security: prevent directory traversal
    if not os.path.abspath(filepath).startswith(os.path.abspath(reports_dir)):
        return jsonify(success=False, message="Invalid file path"), 400

    if not os.path.exists(filepath):
        return jsonify(success=False, message="File not found"), 404

    try:
        os.remove(filepath)
        return jsonify(success=True, message=f"{filename} deleted successfully")
    except Exception as e:
        current_app.logger.error(f"Failed to delete report {filename}: {e}")
        return jsonify(success=False, message=str(e)), 500

def root_redirect():
    """
    Redirects the user to the appropriate page based on their login status.

    Returns:
        Response: A redirection to the dashboard if the user is logged in,
                  otherwise a redirection to the login page.
    """
    if session.get("username"):
        return redirect(url_for("audit.dashboard"))
    return redirect(url_for("login"))

def render_html():
    """
    Renders an HTML file specified by the 'path' query parameter.

    Returns:
        Response: The content of the HTML file or a 404 error if not found.
    """
    file_path = request.args.get("path")
    if not file_path:
        abort(404)

    tmp_dir = tempfile.gettempdir()
    if not os.path.abspath(file_path).startswith(os.path.abspath(tmp_dir)):
        abort(403)

    if not os.path.exists(file_path):
        abort(404)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        response = make_response(content)
        response.headers["Content-Type"] = "text/html"
        return response
    except Exception as e:
        current_app.logger.error(f"Failed to render HTML from {file_path}: {e}")
        abort(500)