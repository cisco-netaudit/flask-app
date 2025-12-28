"""
User management module for a web application.
Handles user initialization, workspace setup, and user-specific data storage.

Classes:
- User: Represents a user with attributes and methods to manage their workspace.
"""


import os
from .localstore import LocalStore

class User:
    """
    Represents a user in the application.
    """
    def __init__(self, username, users_db, **kwargs):
        """
        Initialize a User instance.

        Args:
            username (str): The username of the user.
            users_db (local_store): A dictionary representing the users database.
            **kwargs: Additional user attributes (role, email, firstname, lastname).
        """
        self.username = str(username)
        self.users_db = users_db
        self.role = kwargs.get("role", self.users_db.get(self.username, {}).get("role", "user"))
        self.email = kwargs.get("email", self.users_db.get(self.username, {}).get("email", ""))
        self.firname = kwargs.get("firstname", self.users_db.get(self.username, {}).get("firstname", ""))
        self.lastname = kwargs.get("lastname", self.users_db.get(self.username, {}).get("lastname", ""))
        self.fullname = f"{self.firname} {self.lastname}".strip() if self.firname or self.lastname else self.username

        self.dir = None
        self.reports_dir = None

    def setup_workspace(self, base_dir):
        """
        Set up the user's workspace directory and initialize user-specific data storage.

        Args:
            base_dir (str): The base directory where user workspaces are created.
        """
        self.dir = os.path.join(base_dir, self.username)
        self.reports_dir = os.path.join(self.dir, "reports")
        self.db = LocalStore(os.path.join(self.dir, "account"))
        os.makedirs(self.dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        self.db.update({
            "username": self.username,
            "role": self.role,
            "email": self.email,
            "firstname": self.firname,
            "lastname": self.lastname,
            "fullname": self.fullname,
            "reports_dir": self.reports_dir,
            "theme": "light",
        })
