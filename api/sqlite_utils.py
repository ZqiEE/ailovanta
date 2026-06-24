from __future__ import annotations

import sqlite3
from pathlib import Path


class ClosingConnection(sqlite3.Connection):
    """SQLite connection that closes when leaving a with-block.

    sqlite3.Connection commits or rolls back on __exit__, but it does not close
    the database file. Linux allows deleting open SQLite files, but Windows does
    not. Tests that use TemporaryDirectory need the handle closed before cleanup.
    """

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()
        return False


def connect_sqlite(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(Path(path), factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    return conn
