import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _resolve_data_root() -> str:
    if getattr(sys, "frozen", False):
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return os.path.join(local_appdata, "GeneradorInformes")
        return os.path.join(os.path.expanduser("~"), "GeneradorInformes")
    return BASE_DIR

DATA_ROOT = _resolve_data_root()
DB_PATH = os.path.join(DATA_ROOT, "data", "app.db")

def _seed_db_candidates() -> list[str]:
    if not getattr(sys, "frozen", False):
        return []

    candidates: list[str] = []
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        candidates.append(os.path.join(meipass, "data", "app.db"))

    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(os.path.join(exe_dir, "data", "app.db"))
    candidates.append(os.path.join(os.path.dirname(exe_dir), "app", "data", "app.db"))

    resolved = []
    seen = set()
    for path in candidates:
        full_path = os.path.abspath(path)
        if full_path == os.path.abspath(DB_PATH):
            continue
        if full_path in seen:
            continue
        seen.add(full_path)
        resolved.append(full_path)
    return resolved

def _first_existing_seed_db() -> str | None:
    for candidate in _seed_db_candidates():
        if os.path.exists(candidate):
            return candidate
    return None

def _safe_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        row = conn.execute(f"SELECT COUNT(1) FROM {table}").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0

def _merge_seed_data(seed_db_path: str) -> None:
    if not os.path.exists(seed_db_path):
        return

    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        shutil.copy2(seed_db_path, DB_PATH)
        return

    with sqlite3.connect(DB_PATH) as target_conn, sqlite3.connect(seed_db_path) as seed_conn:
        target_conn.execute("PRAGMA foreign_keys = ON")
        target_conn.executescript(SCHEMA_SQL)
        _ensure_user_columns(target_conn)

        seed_conn.row_factory = sqlite3.Row
        target_conn.row_factory = sqlite3.Row

        target_submissions = _safe_count(target_conn, "submissions")
        if target_submissions == 0:
            seed_rows = seed_conn.execute(
                "SELECT created_at, data_json FROM submissions ORDER BY id ASC"
            ).fetchall()
            if seed_rows:
                target_conn.executemany(
                    "INSERT INTO submissions (created_at, data_json) VALUES (?, ?)",
                    [(row["created_at"], row["data_json"]) for row in seed_rows],
                )

        existing_roles = {
            row["name"]: row["id"]
            for row in target_conn.execute("SELECT id, name FROM roles").fetchall()
        }
        seed_roles = [
            row["name"]
            for row in seed_conn.execute("SELECT name FROM roles ORDER BY id ASC").fetchall()
            if row["name"]
        ]
        for role_name in seed_roles:
            if role_name not in existing_roles:
                cur = target_conn.cursor()
                cur.execute("INSERT INTO roles (name) VALUES (?)", (role_name,))
                existing_roles[role_name] = cur.lastrowid

        existing_users = {
            row["username"]
            for row in target_conn.execute("SELECT username FROM users").fetchall()
        }
        seed_users = seed_conn.execute(
            """
            SELECT
                users.username,
                users.password_hash,
                users.first_name,
                users.last_name,
                users.dependency,
                users.doc_type,
                users.doc_number,
                users.created_at,
                roles.name AS role_name
            FROM users
            JOIN roles ON roles.id = users.role_id
            ORDER BY users.id ASC
            """
        ).fetchall()

        for user in seed_users:
            username = user["username"]
            role_name = user["role_name"]
            if not username or username in existing_users:
                continue
            role_id = existing_roles.get(role_name)
            if not role_id:
                continue
            target_conn.execute(
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
                (
                    username,
                    user["password_hash"],
                    role_id,
                    user["first_name"] or "",
                    user["last_name"] or "",
                    user["dependency"] or "",
                    user["doc_type"] or "",
                    user["doc_number"] or "",
                    user["created_at"] or datetime.utcnow().isoformat(),
                ),
            )
            existing_users.add(username)

        target_conn.commit()

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
    seed_db_path = _first_existing_seed_db()
    if seed_db_path:
        _merge_seed_data(seed_db_path)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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
                users.dependency,
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
