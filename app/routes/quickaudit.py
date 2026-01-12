"""
This module provides views and utilities for the "Quick Audit" audit functionality, including
rendering the interface, executing audits on devices, generating reports, and exporting
audit results to an Excel file.
"""

from flask import render_template, current_app, url_for, request, jsonify, session, send_file
import os
import json
from datetime import datetime
from netcore import XLBW


def render_quickaudit():
    """
    Renders the "Quick Audit" audit page.

    Returns:
        Response: An HTML template rendered with the provided context.
    """
    checks = current_app.checks_db

    kwargs = {
        "breadcrumbs": [
            {"title": "Audit", "url": url_for("audit")},
            {"title": "Quick Audit"}
        ],
        "checks": checks,
        "status_codes": current_app.utils.AUDIT_STATUS_CODES
    }

    return render_template("audit.quickaudit.html", **kwargs)


def quickaudit_run():
    """
    Initiates and executes the "Quick Audit" audit process for the provided devices and checks.

    Returns:
        Response: A JSON response indicating success or failure of the audit process.
    """
    data = request.get_json()
    devices = []

    device_list = data.get("devices", [])
    check_list = data.get("checks", [])
    _session = data.get("session", {})

    session["creds"] = {
        "jumphost_ip": _session.get("jumphost_ip"),
        "jumphost_username": _session.get("jumphost_username"),
        "jumphost_password": _session.get("jumphost_password"),
        "network_username": _session.get("network_username"),
        "network_password": _session.get("network_password"),
    }

    for device in device_list:
        devices.append({
            "device": device,
            "check_list": check_list,
            "session": _session
        })

    context = {}

    audit_service = current_app.modules.AuditService(
        devices, current_app.utils.CHECKS_DIR, current_app.utils.FACTS_DIR, context=context
    )

    audit_service.start_thread_executor()
    audit_service.wait_for_completion()

    report_id  = f"QuickAudit_{datetime.now().strftime('%Y-%m-%d_%H.%M')}.json"
    report_path = os.path.join(session.get("reports_dir"), report_id)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(audit_service.results, f, indent=4)

    session["last_report_path"] = report_path

    return jsonify({
        "success": True,
        "message": "QuickAudit run completed",
    }), 200


def quickaudit_report():
    """
    Retrieves the latest audit report results.

    Returns:
        Response: A JSON response containing the audit results or an error message.
    """
    last_report_path = session.get("last_report_path")

    if not last_report_path:
        return jsonify({"error": "No report found"}), 404

    with open(last_report_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    return jsonify(results)

def export_report():
    """
    Exports the audit results to an Excel file.

    Returns:
        Response: A file download response with the generated Excel report.
    """
    payload = request.get_json()
    if not payload or "data" not in payload:
        return jsonify({"error": "Missing data"}), 400

    data = payload["data"]
    if not data:
        return jsonify({"error": "No data to export"}), 400

    status_codes = current_app.utils.AUDIT_STATUS_CODES

    timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M")
    filename = f"QuickAudit_{timestamp}.xlsx"

    report_dir = session.get("reports_dir")
    os.makedirs(report_dir, exist_ok=True)
    filepath = os.path.join(report_dir, filename)

    wb = XLBW(filepath)
    ws = wb.add_worksheet()

    status_formats = {}
    for code, info in status_codes.items():
        status_formats[code] = wb.add_format({
            "bg_color": info["excel_color"],
            "font_size": "10",
            "font_name": "Segoe UI",
            "font_color": "#000000",
            "valign": "top",
            "text_wrap": True
        })

    headers = ["Device", "Login", "Overall"]
    first_result = next(iter(data.values()), None)
    if first_result:
        headers.extend(
            check.get("checkName", check)
            for checkfile, check in first_result.get("checks", {}).items()
        )

    ws.write_row(0, 0, headers, wb.ftheader1)
    row = 1
    for device, result in data.items():
        ws.write(row, 0, result["displayName"], wb.ftbody)
        if result.get("login"):
            ws.write(row, 1, "Success", status_formats.get(1))
        else:
            ws.write(row, 1, "Failed", status_formats.get(2))
        overall_status = result.get("status", 0)
        ws.write(row, 2, status_codes[overall_status]["label"].title(), status_formats.get(overall_status))
        col = 3
        for check, check_result in result.get("checks", {}).items():
            check_status = check_result.get("status", 0)
            ws.write(row, col, status_codes[check_status]["label"].title(), status_formats.get(check_status))
            col += 1
        row += 1
    wb.close()

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )