"""
This module provides utility functions for managing and interacting 
with datasets, checks, devices, users, and other components within 
a Flask-based application. It includes functions for CRUD operations, 
data persistence, and integration with external systems (e.g., AI models).
"""

import os
import json
import importlib.util
import logging
import bcrypt
import io
import zipfile
import datetime

from flask import jsonify, current_app, request, send_file, session


def get_dataset(dataset):
    """
    Retrieve the specified dataset from the application's local store.
    Args:
        dataset (str): The name of the dataset to retrieve (e.g., 'checks', 'devices').
    Returns:
        Response: A Flask JSON response containing the requested dataset.
    """

    db = getattr(current_app, f"{dataset}_db", None)
    if db is not None:
        return jsonify(db.as_dict())
    return jsonify(error="Dataset not found"), 404

def scan_checks():
    """
    Recursively scan the checks directory for Python check scripts,
    load their metadata, and return a JSON dictionary keyed by
    relative file paths.
    """
    checks_dir = current_app.utils.CHECKS_DIR
    checks = {}

    for root, dirs, files in os.walk(checks_dir):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("__"):
                file_path = os.path.join(root, filename)

                # Generate path relative to the checks root
                rel_path = os.path.relpath(file_path, checks_dir)

                module_name = rel_path.replace(os.sep, "_").replace(".py", "")

                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)

                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    logging.warning(f"Skipping {rel_path}: import error: {e}")
                    continue

                check_class = getattr(module, "CHECK_CLASS", None)
                if not check_class:
                    logging.warning(f"Skipping {rel_path}: CHECK_CLASS not found")
                    continue

                metadata = {
                    "name": getattr(check_class, "NAME", ""),
                    "version": getattr(check_class, "VERSION", ""),
                    "tags": getattr(check_class, "TAGS", []),
                    "description": getattr(check_class, "DESCRIPTION", ""),
                    "complexity": getattr(check_class, "COMPLEXITY", 1),
                    "author": getattr(check_class, "AUTHOR", "Unknown"),
                }

                # Read full source code
                with open(file_path, "r", encoding="utf-8") as file:
                    metadata["code"] = file.read()

                checks[rel_path] = metadata
    return jsonify(checks)


def export_checks():
    """
    Export selected check scripts as a ZIP file.

    Returns:
        Response: A Flask response containing the ZIP file for download.
    """
    payload = request.get_json()
    selected_checks = payload.get("checks", [])
    checks_dir = current_app.utils.CHECKS_DIR

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for check_filename in selected_checks:
            file_path = os.path.join(checks_dir, check_filename)
            if os.path.exists(file_path):
                zip_file.write(file_path, arcname=check_filename)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="exported_checks.zip"
    )

def generate_check():
    """
    Generate a Python check script using AI, based on the provided 
    specifications in the request body.

    Returns:
        Response: A Flask JSON response containing either the generated 
                  check code or an error message.
    """
    data = request.json
    description = data.get("description")
    sample_output = data.get("sampleOutput", "")

    user_prompt = current_app.utils.CHECK_PROMPT_TEMPLATE.replace(
        "<INSERT_DESCRIPTION_HERE>", description
    ).replace(
        "<INSERT_SAMPLE_OUTPUT_HERE>", sample_output
    )

    if current_app.azureai.ready:
        try:
            code = current_app.azureai.ask(
                system_prompt="You are a Python developer generating a Netaudit check.",
                user_prompt=user_prompt,
                format="code"
            )
            return jsonify({"status": "success", "code": code})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "error", "message": "AI client not configured."})


def delete_dataset_items(dataset):
    """
    Delete items from a specified dataset.

    Args:
        dataset (str): The dataset name (e.g., 'checks', 'devices').

    Returns:
        Response: A Flask JSON response listing deleted items.
    """
    payload = request.get_json()
    keys_to_delete = payload.get("keys", [])
    deleted = []

    for key in keys_to_delete:
        if dataset == "checks":
            file_path = os.path.join(current_app.utils.CHECKS_DIR, key)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted.append(key)
                except Exception as e:
                    return jsonify(error=str(e)), 500

            # Remove check from all views
            for view_name in current_app.views_db.keys():
                view_data = current_app.views_db[view_name]
                checks_list = view_data.get("checks", [])
                if key in checks_list:
                    checks_list.remove(key)
                    view_data["checks"] = checks_list
                    current_app.views_db[view_name] = view_data

            current_app.checks_db.pop(key, None)

        elif dataset == "devices":
            for view_name in current_app.views_db.keys():
                view_data = current_app.views_db[view_name]
                devices_list = view_data.get("devices", [])
                if key in devices_list:
                    devices_list.remove(key)
                    view_data["devices"] = devices_list
                    current_app.views_db[view_name] = view_data

            # Remove device files
            os.remove(os.path.join(current_app.utils.RESULTS_DIR, f"{key}.json"))
            os.remove(os.path.join(current_app.utils.RESULTS_DIR, f"{key}.sqlite"))

            current_app.devices_db.pop(key, None)

        elif dataset == "views":
            devices = current_app.views_db.get(key, {}).get("devices", [])
            current_app.views_db.pop(key, None)
            update_device_results_upon_view_change(devices)

        elif dataset == "sessions":
            current_app.sessions_db.pop(key, None)

        elif dataset == "users":
            current_app.users_db.pop(key, None)

        deleted.append(key)

    current_app.checks_db.assign(current_app.routes.scan_checks().get_json())
    logging.info(f"Deleted items from {dataset}: {deleted}")
    return jsonify(deleted=deleted)


def save_dataset_item(dataset):
    """
    Save or update an item in a specified dataset.

    Args:
        dataset (str): The dataset name (e.g., 'checks', 'devices').

    Returns:
        Response: A Flask JSON response confirming the save operation.
    """
    payload = request.get_json()
    key = payload.get("key")
    data = payload.get("data", {})

    if dataset == "checks":
        file_path = os.path.join(current_app.utils.CHECKS_DIR, key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(data)
        current_app.checks_db.assign(current_app.routes.scan_checks().get_json())

    elif dataset == "views":
        # Preserve existing devices list if the view already exists
        existing_view = current_app.views_db.get(key, {})
        data["devices"] = existing_view.get("devices", [])
        current_app.views_db[key] = data  # Re-assign to persist nested structure

        # Update device results based on view changes
        update_device_results_upon_view_change(data["devices"])

    elif dataset == "devices":
        view_names = data.get("view", [])
        devices = key.split(",")
        for device in devices:
            device = device.strip()
            for view_name in view_names:
                view = current_app.views_db.get(view_name, {})
                devices_list = view.get("devices", [])
                if device not in devices_list:
                    devices_list.append(device)
                view["devices"] = devices_list
                current_app.views_db[view_name] = view

            # Remove device from other views
            for other_view_name in current_app.views_db.keys():
                if other_view_name not in view_names:
                    view_data = current_app.views_db[other_view_name]
                    devices_list = view_data.get("devices", [])
                    if device in devices_list:
                        devices_list.remove(device)
                        view_data["devices"] = devices_list
                        current_app.views_db[other_view_name] = view_data

            # Save/update device results (empty dict placeholder)
            save_device_results_util(device, {})
            data.update({"date": datetime.datetime.now().isoformat(), "user": session.get("username", "Unknown")})
            current_app.devices_db.update({device: data})

    elif dataset == "sessions":
        current_app.sessions_db.update({key: data})

    elif dataset == "users":
        password = data.get("password")
        if password:
            hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            data["password"] = hashed_pw.decode("utf-8")
        current_app.users_db.update({key: data})

    logging.info(f"Saved/Updated item in {dataset}: {key}")
    return jsonify(success=True, key=key, data=data)

def update_device_results_upon_view_change(view_devices):
    """
    Update device results when views are modified.
    Args:
        view_devices (list): List of device hostnames/ips associated with the modified view.
    """
    views = current_app.views_db.as_dict()
    all_checks = set()
    for view in views.values():
        for check in view.get("checks", []):
            all_checks.add(check)
    for device in view_devices:
        device_results = get_device_results(device).get_json()
        status = 1
        if not device_results.get("login"):
            status = 2
        for check in list(device_results.get("checks", {}).keys()):
            check_status = device_results["checks"][check].get("status", 0)
            if check not in all_checks:
                device_results["checks"].pop(check, None)
            elif check_status in [2, 5]:
                status = 2
        device_results["status"] = status
        save_device_results_util(device, device_results, clear_missing=True)

def get_device_results(device_id):
    """
    Retrieve results for a specific device.

    Args:
        device_id (str): The device hostname/ip.
    Returns:
        Response: A Flask JSON response containing the device results or an error message.
    """
    db_path = os.path.join(current_app.utils.RESULTS_DIR, device_id)
    device_db = current_app.modules.LocalStore(db_path)
    results = device_db.as_dict()
    device_db.close()

    return jsonify(results)

def save_device_results(device_id):
    """
    Save or update results for a specific device.

    Args:
        device_id (str): The device hostname/ip.
    Returns:
        Response: A Flask JSON response confirming the save operation.
    """
    data = request.get_json()
    success = save_device_results_util(device_id, data)
    if success:
        return jsonify(success=True, device_id=device_id)
    return jsonify(error="Failed to save device results"), 500

def save_followup():
    """
    Save follow-up actions and comments for a list of devices.

    Returns:
        Response: A Flask JSON response indicating success and updated devices.
    """
    data = request.get_json()
    devices_list = data.get("devices", [])
    user_action = data.get("user_action", "").strip()
    user_comments = data.get("user_comments", "").strip()

    if not devices_list:
        return jsonify({"error": "No devices provided"}), 400

    updated_devices = []
    for device_id in devices_list:
        update_data = {
            "user_action": user_action,
            "user_comments": user_comments
        }
        success = save_device_results_util(device_id, update_data)
        if success:
            updated_devices.append(device_id)

    logging.info(f"Follow-up saved for devices: {updated_devices}")
    return jsonify({"success": True, "updated_devices": updated_devices})


def save_device_results_util(device_id, data, clear_missing=False):
    """
    Utility function to save or update device results in a local store.

    Args:
        device_id (str): The device hostname/ip.
        data (dict): The data to update for the device.
        clear_missing (bool): If True, remove keys not present in `data`.

    Returns:
        bool: True if the operation was successful.
    """

    db_path = os.path.join(current_app.utils.RESULTS_DIR, device_id)
    device_db = current_app.modules.LocalStore(db_path)

    if not device_db.as_dict():
        device_db.update({
            "last_audit": "0001-01-01T00:00.000000",
            "login": None,
            "hostname": device_id,
            "raw": {},
            "facts": {},
            "checks": {},
            "status": 0,
            "user_action": "",
            "user_comments": ""
        })

    if clear_missing:
        merged_data = data.copy()

    else:
        existing_data = device_db.as_dict()
        merged_data = existing_data.copy()

        for k, v in data.items():
            if isinstance(v, dict) and isinstance(merged_data.get(k), dict):
                merged_data[k].update(v)
            else:
                merged_data[k] = v

    device_db.update(merged_data)
    logging.info(f"Device results saved for {device_id}")
    device_db.close()
    return True



