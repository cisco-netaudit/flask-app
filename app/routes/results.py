"""
This module provides audit result views and dashboard auditing capabilities for devices.
"""

from flask import current_app, render_template, url_for, request, jsonify
from datetime import datetime
import logging


def render_audit_results_view(view_name):
    """
    Render the audit results view for the specified view name.

    Parameters:
        view_name (str): The name of the view for which audit results are rendered.

    Returns:
        str: The rendered HTML template.
    """

    views = current_app.views_db.as_dict()
    checks = current_app.checks_db.as_dict()
    
    view_devices = views.get(view_name, {}).get("devices", [])
    view_checks = views.get(view_name, {}).get("checks", [])
    check_names = [checks.get(check, {}).get("name", check) for check in view_checks]

    kwargs = {
        "columns": ["Hostname", "Overall", "Action Taken"] + check_names,
        "breadcrumbs": [
            {"title": "Audit", "url": url_for("audit")},
            {"title": "Results", "url": url_for("audit.results.view", view_name=next(iter(views)))},
            {"title": view_name}
        ],
        "std_user_actions": current_app.utils.USER_ACTIONS,
        "status_codes": current_app.utils.AUDIT_STATUS_CODES,
        "view": view_name
    }

    dataset = []
    for device_id in view_devices:
        device_data = current_app.routes.get_device_results(device_id).get_json()
        checks_data = device_data.get("checks", {})

        dataset.append({
            "device_id": device_id,
            "device_data": device_data,
            "last_audit": datetime.fromisoformat(
                device_data.get("last_audit", "0001-01-01T00:00.000000").split(".")[0]
            ).strftime("%d-%b-%Y %H:%M"),
            "checks": [checks_data.get(chk, {}).get("status", 0) for chk in view_checks]
        })
    kwargs["dataset"] = dataset

    return render_template("audit.results.view.html", **kwargs)


def render_audit_results_device(device_id):
    """
    Render the audit results for a specific device.

    Parameters:
        device_id (str): The ID of the device for which audit results are rendered.

    Returns:
        str: The rendered HTML template.
    """
    checks = current_app.checks_db.as_dict()
    devices = current_app.devices_db.as_dict()
    view = request.args.get("view")

    device_data = current_app.routes.get_device_results(device_id).get_json()

    kwargs = {
        "columns": ["Check Name", "Status", "Observation", "Comments"],
        "breadcrumbs": [
            {"title": "Audit", "url": url_for("audit")},
            {"title": "Results", "url": url_for("audit.results.view", view_name=next(iter(current_app.views_db.as_dict())))},
            {"title": view, "url": url_for("audit.results.view", view_name=view)},
            {"title": device_data.get("hostname", device_id)}
        ],
        "device_id": device_id,
        "device_data": device_data,
        "std_user_actions": current_app.utils.USER_ACTIONS,
        "status_codes": current_app.utils.AUDIT_STATUS_CODES,
        "view": view,
        "date_added": datetime.fromisoformat(devices.get(device_id, {}).get("date", "").split(".")[0]).strftime(
            "%d-%b-%Y %H:%M"
        ),
        "last_audit": datetime.fromisoformat(
            device_data.get("last_audit", "0001-01-01T00:00.000000").split(".")[0]
        ).strftime("%d-%b-%Y %H:%M"),
    }

    dataset = []
    view_checks = current_app.views_db.as_dict().get(view, {}).get("checks", [])
    for check in view_checks:
        check_data = device_data.get("checks", {}).get(check, {})
        if checks.get(check):
            dataset.append({
                "Check Name": checks.get(check, {}).get("name", check),
                "Status": check_data.get("status", 0),
                "Observation": check_data.get("observation", ""),
                "Comments": "\n".join(check_data.get("comments", [])),
            })

    kwargs["dataset"] = dataset

    return render_template("audit.results.device.html", **kwargs)


def results_run():
    """
    Execute an audit on a list of devices based on the provided view and return the results.

    Returns:
        Response: JSON response indicating success or failure of the audit operation.
    """
    managed_views = current_app.views_db.as_dict()
    managed_devices = current_app.devices_db.as_dict()
    managed_sessions = current_app.sessions_db.as_dict()
    data = request.get_json()
    device_list = data.get("devices", [])
    view = data.get("view", None)

    devices = []

    for device_id in device_list:
        check_list = managed_views.get(view, {}).get("checks", []) if view else []
        session = managed_sessions.get(managed_devices.get(device_id, {}).get("session"), {})
        for field in ["jumphost_password", "network_password"]:
            session[field] = current_app.cipher.decrypt(session[field])
        devices.append({
            "device": device_id,
            "check_list": check_list,
            "session": session,
        })

    context = {}

    audit_service = current_app.modules.AuditService(
        devices, current_app.utils.CHECKS_DIR, current_app.utils.FACTS_DIR, context=context
    )

    audit_service.start_thread_executor()
    audit_service.wait_for_completion()

    for device_id, results in audit_service.results.items():
        current_app.routes.save_device_results_util(device_id, results)
        logging.info(f"Audit results written for device '{device_id}'")

    return jsonify({"success": True, "message": "Audit completed"}), 200