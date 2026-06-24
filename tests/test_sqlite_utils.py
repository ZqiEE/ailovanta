import os
import tempfile

from api.sqlite_utils import connect_sqlite


def test_connect_sqlite_closes_file_handle_for_windows_cleanup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "temporary.sqlite3")
        with connect_sqlite(db_path) as conn:
            conn.execute("CREATE TABLE demo (id TEXT PRIMARY KEY)")
            conn.execute("INSERT INTO demo (id) VALUES ('ok')")

        os.remove(db_path)
        assert not os.path.exists(db_path)
