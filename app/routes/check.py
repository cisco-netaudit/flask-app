"""
Routes for managing and testing network device checks, including
preparing test instances, running handlers, and managing Git repositories.
"""

import io
import os
import shutil
import sys
import stat
import traceback
import subprocess
from flask import request, jsonify, session, current_app

# Runtime in-memory store for active checks (per browser session)
CHECK_TEST_SESSIONS = {}

def safe_exec_check(code: str):
    """
    Execute the provided code securely in a clean local environment
    and return the CHECK_CLASS object.
    """
    local_env = {}
    sys_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        exec(code, local_env)
    finally:
        sys.stdout = sys_stdout

    cls = local_env.get("CHECK_CLASS")
    if not cls:
        raise ValueError("CHECK_CLASS not defined in provided code")

    return cls

def prepare_test():
    """
    Create a new check instance, store it in session,
    and return its initial REQUESTS & RESULTS.
    """
    data = request.get_json()
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "Empty check code"}), 400

    try:
        cls = safe_exec_check(code)
        check = cls(device="TestDevice", context={})

        # Persistent ID across reloads (string to avoid int mismatch)
        session_id = str(id(check))

        # Store in memory + browser session
        CHECK_TEST_SESSIONS[session_id] = check
        session["test_session_id"] = session_id

        return jsonify({
            "session_id": session_id,
            "requests": check.REQUESTS,
            "results": check.RESULTS
        })

    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


def run_handler():
    """
    Run the current handler using the provided sample output,
    update state, and return the next REQUESTS & RESULTS.
    """
    data = request.get_json()
    sample_output = data.get("sample_output", "")

    # Retrieve same session ID each handler run
    session_id = session.get("test_session_id")
    if not session_id:
        return jsonify({"error": "Test session expired or missing"}), 400

    # Retrieve check instance
    check = CHECK_TEST_SESSIONS.get(session_id)
    if not check:
        return jsonify({"error": "Test session expired or missing"}), 400

    try:
        handler_name = check.REQUESTS.get("handler")
        if not handler_name:
            return jsonify({"error": "No handler defined in REQUESTS"}), 400

        if not hasattr(check, handler_name):
            return jsonify({"error": f"Handler '{handler_name}' not found"}), 400

        handler = getattr(check, handler_name)
        req = check.REQUESTS

        # Execute handler with provided sample output
        handler(req["device"], req["command"], sample_output)

        return jsonify({
            "session_id": session_id,
            "results": check.RESULTS,
            "requests": check.REQUESTS
        })

    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


def scan_git_repos():
    """
    Scan the checks directory for Git repositories and return their paths and remote URLs.
    """
    git_repos = []

    for root, dirs, files in os.walk(current_app.utils.CHECKS_DIR):
        if ".git" in dirs:
            try:
                remote_url = subprocess.check_output(
                    ["git", "-C", root, "config", "--get", "remote.origin.url"],
                    text=True).strip()
            except subprocess.CalledProcessError:
                remote_url = ""
            git_repos.append({
                "local_path": root,
                "remote_url": remote_url
            })
            dirs.remove(".git")
    return jsonify(git_repos), 200


def check_git_repo_status():
    """
    Returns whether the local repo is behind remote 'origin/master'.
    Response: { "update_available": true/false }
    """
    data = request.get_json()
    local_path = data.get("local_path", "").strip()

    if not local_path:
        return jsonify({"error": "Repository path is required"}), 400

    full_path = os.path.join(current_app.utils.CHECKS_DIR, local_path)

    if not os.path.isdir(os.path.join(full_path, ".git")):
        return jsonify({"error": "Not a Git repository"}), 400

    try:
        # Get latest info from remote
        subprocess.check_output(
            ["git", "fetch"],
            cwd=full_path,
            text=True,
            stderr=subprocess.STDOUT
        )

        # Compare local master vs origin/master
        result = subprocess.check_output(
            ["git", "rev-list", "--left-right", "--count", "master...origin/master"],
            cwd=full_path,
            text=True
        ).strip()

        ahead, behind = map(int, result.split())

        return jsonify({"update_available": behind > 0})

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Git error", "details": e.output}), 500

def pull_git_repo():
    """
    Pull the latest changes for a Git repository in the checks directory.
    """
    data = request.get_json()
    local_path = data.get("local_path", "").strip()

    if not local_path:
        return jsonify({"error": "Repository path is required"}), 400

    if not os.path.isdir(os.path.join(local_path, ".git")):
        return jsonify({"error": "Specified path is not a Git repository"}), 400

    try:
        output = subprocess.check_output(
            ["git", "pull"],
            cwd=local_path,
            text=True,
            stderr=subprocess.STDOUT
        )
        current_app.checks_db.assign(current_app.routes.scan_checks().get_json())
        return jsonify({"message": f"Successfully pulled updates:\n{output}"}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Git pull failed: {e.output}"}), 500

def clone_git_repo():
    """
    Clone a Git repository into the checks directory.
    """
    data = request.get_json()
    remote_url = data.get("remote_url", "").strip()
    local_repo_name = data.get("local_repo_name", "").strip()

    if not remote_url:
        return jsonify({"error": "Repository URL is required"}), 400

    try:
        subprocess.check_output(
            ["git", "clone", remote_url, local_repo_name],
            cwd=current_app.utils.CHECKS_DIR,
            text=True,
            stderr=subprocess.STDOUT
        )
        current_app.checks_db.assign(current_app.routes.scan_checks().get_json())
        return jsonify({"message": f"Successfully cloned {remote_url}"}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Git clone failed: {e.output}"}), 500


def delete_git_repo():
    """
    Delete a Git repository safely, including read-only .git objects (Windows).
    """

    def _remove_readonly(func, path, exc_info):
        """
        Clear read-only attribute and retry.
        """
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            raise

    data = request.get_json()
    local_path = data.get("local_path", "").strip()

    if not local_path:
        return jsonify({"error": "Repository path is required"}), 400

    if not os.path.isdir(local_path):
        return jsonify({"error": "Specified path does not exist"}), 400

    try:
        shutil.rmtree(local_path, onerror=_remove_readonly)
        current_app.checks_db.assign(current_app.routes.scan_checks().get_json())
        return jsonify({"message": f"Successfully deleted repository at {local_path}"}), 200

    except Exception as e:
        return jsonify({
            "error": f"Failed to delete repository: {str(e)}"
        }), 500