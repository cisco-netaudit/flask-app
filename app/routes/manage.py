"""
Module for rendering various management views in a Flask application.
The module provides functions to render pages for managing views, devices,
checks, sessions, and users in the application.
"""

from datetime import datetime
import logging

from flask import render_template, current_app, url_for, session

def render_manage_views():
    """
    Render the 'Manage Views' page.

    Returns:
        str: Rendered HTML for the manage views page.
    """
    views = current_app.views_db.as_dict()
    checks = current_app.checks_db.as_dict()

    kwargs = {
        "add_text": "Add View",
        "columns": ["Name", "Checks"],
        "breadcrumbs": [
            {"title": "Manage", "url": url_for("manage.views")},
            {"title": "Views"},
        ],
    }
    kwargs["view_icons"] = current_app.utils.VIEW_ICONS

    dataset = []
    for name, view_data in views.items():
        checks_list = [
            {
                "name": checks[chk]["name"],
                "description": checks[chk]["description"],
            }
            for chk in view_data.get("checks", [])
            if checks.get(chk)
        ]
        icon = view_data.get("icon")
        dataset.append({"Name": name, "Icon":icon, "Checks": checks_list})

    kwargs["dataset"] = dataset
    return render_template("manage.views.html", **kwargs)


def render_manage_devices():
    """
    Render the 'Manage Devices' page.

    Returns:
        str: Rendered HTML for the manage devices page.
    """
    devices = current_app.devices_db.as_dict()
    sessions = current_app.sessions_db.as_dict()
    views = current_app.views_db.as_dict()

    kwargs = {
        "add_text": "Add Device(s)",
        "columns": [
            "Hostname",
            "View(s)",
            "Session",
            "Date Added",
            "Created By",
        ],
        "dataset": [
            {
                "Hostname": hostname,
                "View(s)": ", ".join(data.get("view", [])),
                "Session": data.get("session", "None"),
                "Date Added": datetime.fromisoformat(
                    data.get("date", "").split(".")[0]
                ).strftime("%d-%b-%Y %H:%M"),
                "Created By": data.get("user", ""),
            }
            for hostname, data in devices.items()
        ],
        "breadcrumbs": [
            {"title": "Manage", "url": url_for("manage.views")},
            {"title": "Devices"},
        ],
        "fields": ["Hostname", "Device Type", "View", "Session"],
        "sessions": list(sessions.keys()),
        "view_list": list(views.keys()),
        "current_user": session.get("username", "admin"),
    }

    return render_template("manage.devices.html", **kwargs)


def render_manage_checks():
    """
    Render the 'Manage Checks' page.

    Returns:
        str: Rendered HTML for the manage checks page.
    """
    checks = current_app.checks_db.as_dict()

    kwargs = {
        "add_text": "Add Check",
        "columns": ["Filepath", "Name", "Description", "Author"],
        "dataset": [
            {
                "Name": chk.get("name", "Unnamed Check"),
                "Filepath": filename,
                "Description": chk.get("description", "No description available."),
                "Author": chk.get("author", "Unknown")
                .strip(),
            }
            for filename, chk in checks.items()
        ],
        "breadcrumbs": [
            {"title": "Manage", "url": url_for("manage.views")},
            {"title": "Checks"},
        ],
        "ai_client_ready": current_app.azureai.is_ready(),
        "status_codes": current_app.utils.AUDIT_STATUS_CODES,
    }

    return render_template("manage.checks.html", **kwargs)


def render_manage_sessions():
    """
    Render the 'Manage Sessions' page.

    Returns:
        str: Rendered HTML for the manage sessions page.
    """
    sessions = current_app.sessions_db.as_dict()

    kwargs = {
        "add_text": "Add Session",
        "columns": ["Name", "JS Hostname", "JS Username", "Network Username"],
        "dataset": [
            {
                "Name": name,
                "JS Hostname": sess.get("jumphost_ip", "Unknown"),
                "JS Username": sess.get("jumphost_username", "Unknown"),
                "Network Username": sess.get("network_username", "Unknown"),
            }
            for name, sess in sessions.items()
        ],
        "breadcrumbs": [
            {"title": "Manage", "url": url_for("manage.views")},
            {"title": "Sessions"},
        ],
    }

    return render_template("manage.sessions.html", **kwargs)


def render_manage_users():
    """
    Render the 'Manage Users' page.

    Returns:
        str: Rendered HTML for the manage users page.
    """
    users = current_app.users_db.as_dict()

    kwargs = {
        "add_text": "Add Admin",
        "columns": [
            "Username",
            "Display Name",
            "Role",
            "Email",
            "Last Login",
        ],
        "dataset": [
            {
                "Username": username,
                "Display Name": f"{user_data.get('firstname', '')} {user_data.get('lastname', '')}".strip()
                or "N/A",
                "Role": user_data.get("role", "Unknown"),
                "Email": user_data.get("email", "Unknown"),
                "Last Login": datetime.fromisoformat(user_data.get("last_login", "").split(".")[0]).strftime("%d-%b-%Y %H:%M") if user_data.get("last_login") else "Never",
            }
            for username, user_data in users.items()
        ],
        "breadcrumbs": [
            {"title": "Manage", "url": url_for("manage.views")},
            {"title": "Users"},
        ],
    }

    return render_template("manage.users.html", **kwargs)