"""
localstore.py

A lightweight, persistent key–value store for Python applications.

LocalStore provides a simple dictionary-like interface backed by SQLite for
durability, while maintaining an automatically synced JSON file for human-readable
inspection or debugging.

Ideal for Flask or desktop apps that need small, local, persistent databases.
"""

import os
import json
from threading import RLock
from sqlitedict import SqliteDict


class LocalStore:
    """
    A persistent, SQLite-backed key–value store with a mirrored JSON view.

    This class behaves like a regular Python dictionary but stores data
    permanently in an SQLite database. Additionally, it keeps a JSON file
    automatically synchronized for easy viewing or manual edits.
    """

    def __init__(self, base_path: str, autocommit: bool = True, recreate=False):
        """
        Initialize the store.

        Args:
            base_path (str): Base path (without extension) for data files.
                             Example: "data/app_settings"
                             Creates:
                                 - "data/app_settings.sqlite"
                                 - "data/app_settings.json"
            autocommit (bool): If True, commits each write immediately.
                               If False, commits only when .commit() or .close() is called.
        """
        self.db_path = base_path + ".sqlite"
        self.json_path = base_path + ".json"
        self.autocommit = autocommit
        self._lock = RLock()

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Recreate files if requested
        if recreate:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            if os.path.exists(self.json_path):
                os.remove(self.json_path)

        # Initialize SQLite-backed dictionary
        self._db = SqliteDict(self.db_path, autocommit=self.autocommit)
        self._sync_to_json()

    # Internal helpers
    def _sync_to_json(self) -> None:
        """Write the full store contents to the JSON mirror file."""
        with self._lock:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(dict(self._db), f, indent=4, ensure_ascii=False)

    def _commit_and_sync(self) -> None:
        """Commit to SQLite and update the JSON mirror."""
        if not self.autocommit:
            self._db.commit()
        self._sync_to_json()

    # Dictionary-like API
    def __getitem__(self, key):
        """Return the value for a given key."""
        return self._db[key]

    def __setitem__(self, key, value):
        """Set a key–value pair and sync to disk."""
        with self._lock:
            self._db[key] = value
            self._commit_and_sync()

    def __delitem__(self, key):
        """Delete a key–value pair."""
        with self._lock:
            del self._db[key]
            self._commit_and_sync()

    def __contains__(self, key) -> bool:
        """Return True if key exists in store."""
        return key in self._db

    def __len__(self) -> int:
        """Return total number of stored keys."""
        return len(self._db)

    def get(self, key, default=None):
        """Return the value for key if present, else default."""
        with self._lock:
            return self._db.get(key, default)

    def update(self, data_dict: dict) -> None:
        """Update multiple key–value pairs at once."""
        with self._lock:
            self._db.update(data_dict)
            self._commit_and_sync()

    def assign(self, data_dict: dict) -> None:
        """Clear the store and update with new key–value pairs."""
        self.clear()
        self._db.update(data_dict)
        self._commit_and_sync()

    def pop(self, key, default=None):
        """Remove and return value for key (or default if missing)."""
        value = self._db.pop(key, default)
        self._commit_and_sync()
        return value

    def popitem(self):
        """Remove and return the last inserted key–value pair."""
        item = self._db.popitem()
        self._commit_and_sync()
        return item

    def clear(self) -> None:
        """Remove all entries from the store."""
        with self._lock:
            self._db.clear()
            self._commit_and_sync()

    def keys(self):
        """Return a list of all keys."""
        with self._lock:
            return list(self._db.keys())

    def values(self):
        """Return a list of all values."""
        return list(self._db.values())

    def items(self):
        """Return a list of (key, value) pairs."""
        with self._lock:
            return list(self._db.items())

    def as_dict(self) -> dict:
        """Return the store’s full contents as a Python dictionary."""
        with self._lock:
            return dict(self._db.items())

    def delete(self) -> None:
        """Delete the SQLite and JSON files associated with this store."""
        self.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.json_path):
            os.remove(self.json_path)

    # Lifecycle methods
    def commit(self) -> None:
        """Manually commit current changes and sync JSON."""
        self._commit_and_sync()

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._db.close()

    # Context manager support
    def __enter__(self):
        """Enable use within a context block."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit and close when exiting context."""
        self._commit_and_sync()
        self.close()
