"""
File system utility functions for managing directories and JSON files.
"""

import os
import logging


def ensure_directories_exist(paths):
    """
    Ensures that the specified directories exist. Creates them if they are missing.

    Args:
        paths (list): A list of directory paths to check/create.
    """
    for dir_path in paths:
        os.makedirs(dir_path, exist_ok=True)
        logging.debug(f"Directory ensured: {dir_path}")
