"""
This module defines path constants for project directories and key JSON file locations used across the application.
"""

import os

# Define the root directory of the project (two levels up from this file)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Define the home directory for netaudit (a hidden directory in the user's home)
NETAUDIT_HOME = os.path.join(os.path.expanduser("~"), ".netaudit")
GLOBAL_LOGGER = os.path.join(NETAUDIT_HOME, "netaudit.log")

# Define data-related directories/files
DATA_DIR = os.path.join(NETAUDIT_HOME, "data")
STORE_DIR = os.path.join(DATA_DIR, "store")
CHECKS_DIR = os.path.join(DATA_DIR, "checks")
FACTS_DIR = os.path.join(DATA_DIR, "facts")
RESULTS_DIR = os.path.join(DATA_DIR, "results")

# Define paths for individual JSON files in the store directory
VIEWS_DB = os.path.join(STORE_DIR, "views")
DEVICES_DB = os.path.join(STORE_DIR, "devices")
CHECKS_DB = os.path.join(STORE_DIR, "checks")
SESSIONS_DB = os.path.join(STORE_DIR, "sessions")
USERS_DB = os.path.join(STORE_DIR, "users")

# Define user-specific directory
USERS_DIR = os.path.join(NETAUDIT_HOME, "users")

# Define project specific space
PROJECT_DIR = os.path.join(NETAUDIT_HOME, "project")