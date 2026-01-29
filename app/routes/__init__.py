"""
Module to import and aggregate various view and utility functions from different application modules.
This facilitates organized access and modular code management.
"""

# Importing utility functions and views from the base module.
from .base import (
    activity,
    set_theme,
    update_profile,
    get_reports,
    delete_report,
    download_report,
    root_redirect,
    render_html
)

# Importing authentication and authorization views and decorators.
from .login import (
    render_login,
    render_register,
    logout,
    login_required,
    admin_required,
    superadmin_required
)

# Importing the dashboard rendering function.
from .dashboard import render_dashboard

# Importing audit results rendering and processing views.
from .results import (
    render_audit_results_view,
    render_audit_results_device,
    snap_audit_results_device,
    results_run,
)

# Importing views and utilities for running audits and generating reports.
from .quickaudit import (
    render_quickaudit,
    quickaudit_run,
    quickaudit_report,
    export_report,
)

# Importing management views for various system components like devices and users.
from .manage import (
    render_manage_views,
    render_manage_checks,
    render_manage_sessions,
    render_manage_devices,
    render_manage_users,
)

# Importing data processing and management utilities.
from .data import (
    get_dataset,
    scan_checks,
    export_checks,
    generate_check,
    delete_dataset_items,
    save_dataset_item,
    get_device_results,
    save_device_results,
    save_followup,
    save_device_results_util,
)

# Importing check testing and Git repository management functions.
from .check import (
    prepare_test,
    run_handler,
    scan_git_repos,
    check_git_repo_status,
    pull_git_repo,
    clone_git_repo,
    delete_git_repo
)