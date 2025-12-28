"""
Module for authentication providers and manager.

This module provides pluggable authentication providers:
1. Local (JSON-based storage)
2. Remote SSH-based authentication
3. Single Sign-On (SSO)

It also includes an authentication manager to unify access to
different providers.
"""

import paramiko
import bcrypt
from abc import ABC, abstractmethod
from datetime import datetime


class AuthProvider(ABC):
    """
    Abstract base class for authentication providers.
    Each provider must implement the `authenticate` method.
    """

    @abstractmethod
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate a user with the given credentials.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        pass


class LocalAuth(AuthProvider):
    """
    Local JSON-based authentication provider.
    Stores user information in a dictionary.
    """

    def __init__(self, users_db: dict):
        """
        Initialize the LocalAuth provider.

        Args:
            users_db (dict): A dictionary of existing users.
        """
        self.users_db = users_db

    def register(self, **kwargs) -> tuple:
        """
        Register a new user in the local storage.

        Args:
            **kwargs: User fields (firstname, lastname, username, password, email, role).

        Returns:
            tuple: (bool, str): Success status and message.
        """
        firstname = kwargs.get("firstname", "")
        lastname = kwargs.get("lastname", "")
        username = kwargs.get("username")
        password = kwargs.get("password")
        email = kwargs.get("email", "")
        role = kwargs.get("role", "user")

        if username in self.users_db:
            return False, "User already exists"

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        self.users_db[username] = {
            "firstname": firstname,
            "lastname": lastname,
            "password": hashed,
            "email": email,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
        }
        return True, "User registered"

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user and update last_login if successful.

        Args:
            username (str): Username of the user.
            password (str): Password of the user.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        if username not in self.users_db:
            return False

        hashed = self.users_db[username]["password"].encode()
        if bcrypt.checkpw(password.encode(), hashed):
            user_data = self.users_db.get(username)
            user_data["last_login"] = datetime.now().isoformat()
            self.users_db[username] = user_data
            return True
        return False

    def set_role(self, username: str, role: str) -> tuple:
        """
        Update the role of an existing user.

        Args:
            username (str): Username of the user.
            role (str): New role for the user.

        Returns:
            tuple: (bool, str): Success status and message.
        """
        if username not in self.users_db:
            return False, "User not found"
        self.users_db[username]["role"] = role
        return True, f"Role updated to {role}"


    def list_users(self) -> dict:
        """
        List all registered users along with their metadata.

        Returns:
            dict: Dictionary of user information.
        """
        return {
            username: {
                "email": u.get("email"),
                "role": u.get("role"),
                "created_at": u.get("created_at"),
                "last_login": u.get("last_login"),
            }
            for username, u in self.users_db.items()
        }


class RemoteSSHAuth(AuthProvider):
    """
    Remote SSH-based authentication provider.
    Uses Paramiko to connect and verify credentials.
    """

    def __init__(self, hostname: str, port: int = 22):
        """
        Initialize the RemoteSSHAuth provider.

        Args:
            hostname (str): Hostname of the SSH server.
            port (int): Port of the SSH server, default is 22.
        """
        self.hostname = hostname
        self.port = port

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user via SSH.

        Args:
            username (str): SSH username.
            password (str): SSH password.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                self.hostname,
                port=self.port,
                username=username,
                password=password,
                timeout=5
            )
            client.close()
            return True
        except Exception:
            return False


class SSOAuth(AuthProvider):
    """
    Stub for Single Sign-On (SSO) authentication provider.
    """

    def __init__(self, provider: str = "azuread"):
        """
        Initialize the SSOAuth provider.

        Args:
            provider (str): The SSO provider (default is "azuread").
        """
        self.provider = provider

    def authenticate(self, username: str, token: str) -> bool:
        """
        Authenticate user using an SSO token.

        Args:
            username (str): Username of the user (not used).
            token (str): SSO token for authentication.

        Returns:
            bool: True if token is valid, False otherwise.
        """
        return True if token else False


class AuthManager:
    """
    Authentication manager for handling different authentication providers.
    """

    def __init__(self, mode: str = "local", **kwargs):
        """
        Initialize the AuthManager with the specified provider mode.

        Args:
            mode (str): Authentication mode ("local", "ssh", or "sso").
            **kwargs: Provider-specific arguments.
        """
        if mode == "local":
            self.provider = LocalAuth(**kwargs)
        elif mode == "ssh":
            self.provider = RemoteSSHAuth(**kwargs)
        elif mode == "sso":
            self.provider = SSOAuth(**kwargs)
        else:
            raise ValueError("Unsupported auth mode")

    def login(self, username: str, password: str) -> bool:
        """
        Authenticate a user with the current provider.

        Args:
            username (str): Username of the user.
            password (str): Password of the user.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        return self.provider.authenticate(username, password)

    def register(self, **metadata) -> tuple:
        """
        Register a new user if the provider supports registration.

        Args:
            **metadata: User fields for registration.

        Returns:
            tuple: (bool, str): Success status and message, or failure message.
        """
        if hasattr(self.provider, "register"):
            return self.provider.register(**metadata)
        return False, "Register not supported for this auth type"

    def list_users(self) -> dict:
        """
        List all users if the provider supports this operation.

        Returns:
            dict: Dictionary of user information, or an empty dict if unsupported.
        """
        if hasattr(self.provider, "list_users"):
            return self.provider.list_users()
        return {}