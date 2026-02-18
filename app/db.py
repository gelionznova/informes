import json
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "app.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    first_name TEXT NOT NULL DEFAULT '',
    last_name TEXT NOT NULL DEFAULT '',
    dependency TEXT NOT NULL DEFAULT '',
    doc_type TEXT NOT NULL DEFAULT '',
    doc_number TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
"""

def init_db() -> None:
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        _ensure_user_columns(conn)
        conn.commit()

def _ensure_user_columns(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    required = {
        "first_name": "TEXT NOT NULL DEFAULT ''",
        "last_name": "TEXT NOT NULL DEFAULT ''",
        "dependency": "TEXT NOT NULL DEFAULT ''",
        "doc_type": "TEXT NOT NULL DEFAULT ''",
        "doc_number": "TEXT NOT NULL DEFAULT ''",
    }
    for name, definition in required.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")

def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}

def list_roles() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, name FROM roles ORDER BY name ASC").fetchall()
    return [_row_to_dict(row) for row in rows]

def get_role_by_name(name: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT id, name FROM roles WHERE name = ?", (name,)).fetchone()
    return _row_to_dict(row) if row else None

def get_role_by_id(role_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT id, name FROM roles WHERE id = ?", (role_id,)).fetchone()
    return _row_to_dict(row) if row else None

def create_role(name: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO roles (name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid

def update_role(role_id: int, name: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE roles SET name = ? WHERE id = ?", (name, role_id))
        conn.commit()

def delete_role(role_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))
        conn.commit()

def reassign_users_role(old_role_id: int, new_role_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET role_id = ? WHERE role_id = ?",
            (new_role_id, old_role_id),
        )
        conn.commit()

def list_users() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                users.id,
                users.username,
                users.first_name,
                users.last_name,
                users.dependency,
                users.doc_type,
                users.doc_number,
                users.role_id,
                users.created_at,
                roles.name AS role
            FROM users
            JOIN roles ON roles.id = users.role_id
            ORDER BY users.username ASC
            """
        ).fetchall()
    return [_row_to_dict(row) for row in rows]

def list_users_by_role(role_name: str) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                users.id,
                users.username,
                users.first_name,
                users.last_name,
                users.doc_number
            FROM users
            JOIN roles ON roles.id = users.role_id
            WHERE roles.name = ?
            ORDER BY users.first_name ASC, users.last_name ASC
            """,
            (role_name,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]

def get_user_by_username(username: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT
                users.id,
                users.username,
                users.password_hash,
                users.first_name,
                users.last_name,
                users.dependency,
                users.doc_type,
                users.doc_number,
                roles.name AS role
            FROM users
            JOIN roles ON roles.id = users.role_id
            WHERE users.username = ?
            """,
            (username,),
        ).fetchone()
    return _row_to_dict(row) if row else None

def get_user_by_id(user_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT
                users.id,
                users.username,
                users.password_hash,
                users.first_name,
                users.last_name,
                users.dependency,
                users.doc_type,
                users.doc_number,
                roles.name AS role,
                users.role_id
            FROM users
            JOIN roles ON roles.id = users.role_id
            WHERE users.id = ?
            """,
            (user_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None

def create_user(
    username: str,
    password_hash: str,
    role_id: int,
    first_name: str,
    last_name: str,
    dependency: str,
    doc_type: str,
    doc_number: str,
) -> int:
    created_at = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                role_id,
                first_name,
                last_name,
                dependency,
                doc_type,
                doc_number,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (username, password_hash, role_id, first_name, last_name, dependency, doc_type, doc_number, created_at),
        )
        conn.commit()
        return cur.lastrowid

def update_user_role(user_id: int, role_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET role_id = ? WHERE id = ?",
            (role_id, user_id),
        )
        conn.commit()

def update_user(
    user_id: int,
    username: str,
    role_id: int,
    first_name: str,
    last_name: str,
    dependency: str,
    doc_type: str,
    doc_number: str,
    password_hash: str | None,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        if password_hash:
            conn.execute(
                """
                UPDATE users
                SET username = ?, role_id = ?, first_name = ?, last_name = ?, dependency = ?, doc_type = ?, doc_number = ?, password_hash = ?
                WHERE id = ?
                """,
                (username, role_id, first_name, last_name, dependency, doc_type, doc_number, password_hash, user_id),
            )
        else:
            conn.execute(
                """
                UPDATE users
                SET username = ?, role_id = ?, first_name = ?, last_name = ?, dependency = ?, doc_type = ?, doc_number = ?
                WHERE id = ?
                """,
                (username, role_id, first_name, last_name, dependency, doc_type, doc_number, user_id),
            )
        conn.commit()

def delete_user(user_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

def has_any_users() -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(1) AS total FROM users").fetchone()
    return bool(row[0]) if row else False

def save_submission(payload: dict) -> int:
    created_at = datetime.utcnow().isoformat()
    data_json = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO submissions (created_at, data_json) VALUES (?, ?)",
            (created_at, data_json),
        )
        conn.commit()
        return cur.lastrowid

def list_submissions(limit: int = 20) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, created_at, data_json FROM submissions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

    results = []
    for row in rows:
        data = json.loads(row["data_json"])
        results.append({
            "id": row["id"],
            "created_at": row["created_at"],
            "data": data,
        })
    return results

def get_submission(record_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, created_at, data_json FROM submissions WHERE id = ?",
            (record_id,),
        ).fetchone()

    if not row:
        return None

    data = json.loads(row["data_json"])
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "data": data,
    }

def update_submission_data(record_id: int, payload: dict) -> bool:
    data_json = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE submissions SET data_json = ? WHERE id = ?",
            (data_json, record_id),
        )
        conn.commit()
        return cur.rowcount > 0

def delete_submission(record_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM submissions WHERE id = ?", (record_id,))
        conn.commit()
        return cur.rowcount > 0
