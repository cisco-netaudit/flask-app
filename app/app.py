"""
This module defines the FlaskApp class, a customized Flask application
with integrated modules, utilities, and routes for managing authentication, 
data store, and audit operations.
"""

import os
import uuid
import logging
import datetime
from flask import Flask, redirect, url_for, session, flash, request
from . import modules
from . import utils
from . import routes


class FlaskApp(Flask):
    """
    A custom Flask application for managing data stores, authentication,
    and audit-related operations.
    """
    def __init__(self, import_name=__name__, **kwargs):
        """
        Initialize the FlaskApp with custom modules, utilities, and routes.

        Args:
            import_name (str): The name of the application package.
            **kwargs: Additional keyword arguments for Flask initialization.
        """
        super().__init__(import_name, static_folder="static", template_folder="templates", **kwargs)

        self.app_version = "2.0.5"
        self.deployment_stage = os.environ.get("NETAUDIT_DEPLOYMENT_STAGE", "dev")
        self.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")

        self.modules = modules
        self.utils = utils
        self.routes = routes
        self.session_lifetime = datetime.timedelta(minutes=30)
        self.logger = self.modules.StreamLogger(name="NetauditGlobalLogger",
                                                filter_regex="werkzeug",
                                                log_file=self.utils.GLOBAL_LOGGER)
        self.azureai = self.modules.AzureAIClient()
        self.cipher = self.modules.PasswordCipher(key_file=os.path.join(self.utils.NETAUDIT_HOME, "cipher.key"))
        self.user = None
        self.auth = None

        self.setup_server_instance()
        self.setup_datafiles()
        self.setup_localstore()
        self.setup_auth()
        self.setup_routes()
        self.inject_globals()
        self.before_request(self.enforce_session_policies)

    def setup_server_instance(self):
        """
        Ensure a unique server instance ID is set in the environment.
        """
        if not os.environ.get("SERVER_INSTANCE_ID"):
            os.environ["SERVER_INSTANCE_ID"] = uuid.uuid4().hex

        self.server_instance_id = os.environ["SERVER_INSTANCE_ID"]

    def setup_datafiles(self):
        """
        Ensure required directories and JSON data files are present.
        """
        dirs = [
            self.utils.NETAUDIT_HOME,
            self.utils.DATA_DIR,
            self.utils.CHECKS_DIR,
            self.utils.FACTS_DIR,
            self.utils.STORE_DIR,
            self.utils.RESULTS_DIR,
            self.utils.USERS_DIR,
            self.utils.PROJECT_DIR,
        ]
        self.utils.ensure_directories_exist(dirs)

    def setup_localstore(self):
        self.views_db = self.modules.LocalStore(self.utils.VIEWS_DB)
        self.devices_db = self.modules.LocalStore(self.utils.DEVICES_DB)
        self.checks_db = self.modules.LocalStore(self.utils.CHECKS_DB, recreate=True)
        self.sessions_db = self.modules.LocalStore(self.utils.SESSIONS_DB)
        self.users_db = self.modules.LocalStore(self.utils.USERS_DB)

        with self.app_context():
            self.checks_db.update(self.routes.scan_checks().get_json())

    def setup_auth(self):
        """
        Initialize the authentication manager with the specified mode and user database.
        If no users exist, create a default admin user.
        """
        auth_mode = os.getenv("AUTH_MODE", "local")
        self.auth = self.modules.AuthManager(mode=auth_mode, users_db=self.users_db)

        # Create a default admin user if no users exist
        if not self.auth.provider.users_db:
            logging.info("Creating initial admin user...")
            self.auth.provider.register(
                firstname="System",
                lastname="Admin",
                username="admin",
                password="admin123",
                email="admin@localhost",
                role="sysadmin",
            )

    def set_authenticated_user(self, username, password):
        """
        Configure the authenticated user db, logger, and Azure AI client.

        Args:
            username (str): The username of the authenticated user.
            password (str): The password of the authenticated user.
        """
        user = self.modules.User(username, self.users_db)
        user.setup_workspace(self.utils.USERS_DIR)

        if password:
            self.cipher.vault.set(username, password)

        session["username"] = username
        session["role"] = user.role
        session["user_dir"] = user.dir
        session["reports_dir"] = user.reports_dir
        session["server_instance_id"] = self.server_instance_id
        session["last_activity"] = datetime.datetime.utcnow().isoformat()
        self.logger.attach_root()

    def setup_routes(self):
        """
        Define application routes for authentication, audit, management, and data operations.
        """
        self.add_url_rule("/", "root", view_func=self.routes.root_redirect)

        # Base routes
        self.add_url_rule("/activity", "activity", view_func=self.routes.activity)
        self.add_url_rule("/set_theme", "set_theme", view_func=self.routes.set_theme, methods=["POST"])
        self.add_url_rule("/update_profile", "update_profile", view_func=self.routes.update_profile, methods=["POST"])
        self.add_url_rule("/reports", "reports", view_func=self.routes.get_reports)
        self.add_url_rule("/reports/delete/<filename>", "reports.delete", view_func=self.routes.delete_report)
        self.add_url_rule("/reports/download/<filename>", "reports.download", view_func=self.routes.download_report)
        self.add_url_rule("/render_html", "render_html", view_func=self.routes.render_html)

        # Authentication routes
        self.add_url_rule("/login", "login", view_func=self.routes.render_login, methods=["GET", "POST"])
        self.add_url_rule("/register", "register", view_func=self.routes.render_register, methods=["GET", "POST"])
        self.add_url_rule("/logout", "logout", view_func=self.routes.logout)

        # Audit dashboard and results routes
        self.add_url_rule("/audit", "audit", view_func=lambda: redirect(url_for("audit.dashboard")))
        self.add_url_rule("/audit/dashboard", "audit.dashboard", view_func=self.routes.login_required(self.routes.render_dashboard))
        self.add_url_rule("/audit/results/view/<view_name>", "audit.results.view", view_func=self.routes.login_required(self.routes.render_audit_results_view))
        self.add_url_rule("/audit/results/device/<device_id>", "audit.results.device", view_func=self.routes.login_required(self.routes.render_audit_results_device))
        self.add_url_rule("/audit/results/run", "audit.results.run", view_func=self.routes.login_required(self.routes.results_run), methods=["POST"])
        self.add_url_rule("/audit/quickaudit", "audit.quickaudit", view_func=self.routes.login_required(self.routes.render_quickaudit))
        self.add_url_rule("/audit/quickaudit/run", "audit.quickaudit.run", view_func=self.routes.login_required(self.routes.quickaudit_run), methods=["POST"])
        self.add_url_rule("/audit/quickaudit/report", "audit.quickaudit.report", view_func=self.routes.login_required(self.routes.quickaudit_report))
        self.add_url_rule("/audit/quickaudit/export", "audit.quickaudit.export", view_func=self.routes.login_required(self.routes.export_report), methods=["POST"])

        # Management routes
        self.add_url_rule("/manage/views", "manage.views", view_func=self.routes.admin_required(self.routes.render_manage_views))
        self.add_url_rule("/manage/devices", "manage.devices", view_func=self.routes.admin_required(self.routes.render_manage_devices))
        self.add_url_rule("/manage/checks", "manage.checks", view_func=self.routes.admin_required(self.routes.render_manage_checks))
        self.add_url_rule("/manage/checks/scan_repos", "manage.checks.scan_repos", view_func=self.routes.admin_required(self.routes.scan_git_repos))
        self.add_url_rule("/manage/checks/check_repo_status", "manage.checks.check_repo_status", view_func=self.routes.admin_required(self.routes.check_git_repo_status), methods=["POST"])
        self.add_url_rule("/manage/checks/clone_repo", "manage.checks.clone_repo", view_func=self.routes.admin_required(self.routes.clone_git_repo), methods=["POST"])
        self.add_url_rule("/manage/checks/sync_repo", "manage.checks.sync_repo", view_func=self.routes.admin_required(self.routes.pull_git_repo), methods=["POST"])
        self.add_url_rule("/manage/checks/delete_repo", "manage.checks.delete_repo", view_func=self.routes.admin_required(self.routes.delete_git_repo), methods=["POST"])
        self.add_url_rule("/manage/sessions", "manage.sessions", view_func=self.routes.admin_required(self.routes.render_manage_sessions))
        self.add_url_rule("/manage/users", "manage.users", view_func=self.routes.admin_required(self.routes.render_manage_users))

        # Local Store
        self.add_url_rule("/data/store/get/<dataset>", "data.get_dataset", view_func=self.routes.login_required(self.routes.get_dataset))
        self.add_url_rule("/data/store/delete/<dataset>", "data.delete_dataset_items", view_func=self.routes.admin_required(self.routes.delete_dataset_items), methods=["POST"])
        self.add_url_rule("/data/store/save/<dataset>", "data.save_dataset_item", view_func=self.routes.admin_required(self.routes.save_dataset_item), methods=["POST"])

        # Checks
        self.add_url_rule("/data/scan_checks", "data.scan_checks", view_func=self.routes.login_required(self.routes.scan_checks))
        self.add_url_rule("/data/export_checks", "data.export_checks", view_func=self.routes.admin_required(self.routes.export_checks), methods=["POST"])
        self.add_url_rule("/data/generate_check", "data.generate_check", view_func=self.routes.admin_required(self.routes.generate_check), methods=["POST"])
        self.add_url_rule("/check/prepare_test", "check.prepare_test", view_func=self.routes.login_required(self.routes.prepare_test), methods=["POST"])
        self.add_url_rule("/check/run_handler", "check.run_handler", view_func=self.routes.login_required(self.routes.run_handler), methods=["POST"])

        # Results
        self.add_url_rule("/data/results/get/<device_id>", "data.get_results", view_func=self.routes.login_required(self.routes.get_device_results))
        self.add_url_rule("/data/results/save/<device_id>", "data.save_results", view_func=self.routes.login_required(self.routes.save_device_results), methods=["POST"])
        self.add_url_rule("/data/results/followup", "data.save_followup", view_func=self.routes.login_required(self.routes.save_followup), methods=["POST"])

    def inject_globals(self):
        """
        Inject global variables to be accessible in Jinja2 templates.
        """

        @self.context_processor
        def inject_base_globals():
            username = session.get("username")
            user_data = self.users_db.get(username, {}) if username else {}
            return {
                "views": self.views_db,
                "devices": self.devices_db,
                "checks": self.checks_db,
                "sessions": self.sessions_db,
                "user": user_data,
                "theme": user_data.get("theme", "light"),
                "user_display_name": f"{user_data.get('firstname', '')} {user_data.get('lastname', '')}".strip() or (username or "Admin"),
                "app_version": self.app_version,
                "deployment_stage": self.deployment_stage
            }

    def enforce_session_policies(self):
        """
        Enforce session policies such as server restart detection and inactivity timeout.
        """

        if request.endpoint in self.utils.EXEMPT_ENDPOINTS:
            return

        # Server restart detection
        if session.get("server_instance_id") != self.server_instance_id:
            session.clear()
            flash("Server restarted. Please log in again.", "info")
            return redirect(url_for("login"))

        # Not logged in
        if not session.get("username"):
            return

        # Inactivity timeout
        now = datetime.datetime.utcnow()
        last_activity = session.get("last_activity")

        if last_activity:
            last_activity = datetime.datetime.fromisoformat(last_activity)
            if now - last_activity > self.session_lifetime:
                session.clear()
                flash("Session expired due to inactivity.", "info")
                return redirect(url_for("login"))

        session["last_activity"] = now.isoformat()
        session.permanent = True