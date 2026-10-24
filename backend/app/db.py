import json
import re
import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_readings_metric_ts ON readings (metric, ts);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT NOT NULL DEFAULT '{}',
    acknowledged INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    method TEXT NOT NULL,
    user TEXT,
    success INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lab_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    result TEXT NOT NULL,
    target TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

METRIC_RE = re.compile(r"^[a-z0-9_]{1,32}$")


def valid_metric(name: str) -> bool:
    return bool(METRIC_RE.match(name))


class Database:
    """A small SQLite wrapper. Every query uses placeholders, never string building."""

    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            if path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def _run(self, sql: str, params: tuple = ()):
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    def _all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    # readings
    def add_reading(self, metric: str, value: float, ts: float) -> None:
        self._run("INSERT INTO readings (ts, metric, value) VALUES (?, ?, ?)", (ts, metric, value))

    def readings(self, metric: str, limit: int, since: float = 0.0) -> list[dict]:
        rows = self._all(
            "SELECT ts, value FROM readings WHERE metric = ? AND ts >= ? ORDER BY ts DESC LIMIT ?",
            (metric, since, limit),
        )
        return [{"ts": r["ts"], "value": r["value"]} for r in reversed(rows)]

    # alerts
    def add_alert(self, ts: float, type_: str, severity: str, message: str, data: dict) -> int:
        cur = self._run(
            "INSERT INTO alerts (ts, type, severity, message, data) VALUES (?, ?, ?, ?, ?)",
            (ts, type_, severity, message, json.dumps(data)),
        )
        return int(cur.lastrowid)

    def alerts(self, limit: int, only_open: bool = False) -> list[dict]:
        sql = "SELECT * FROM alerts"
        if only_open:
            sql += " WHERE acknowledged = 0"
        sql += " ORDER BY id DESC LIMIT ?"
        return [self._alert_row(r) for r in self._all(sql, (limit,))]

    def ack_alert(self, alert_id: int) -> bool:
        cur = self._run("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
        return cur.rowcount > 0

    @staticmethod
    def _alert_row(r: sqlite3.Row) -> dict:
        return {
            "id": r["id"],
            "ts": r["ts"],
            "type": r["type"],
            "severity": r["severity"],
            "message": r["message"],
            "data": json.loads(r["data"]),
            "acknowledged": bool(r["acknowledged"]),
        }

    # door access
    def add_access(self, ts: float, method: str, user: str | None, success: bool) -> None:
        self._run(
            "INSERT INTO access_log (ts, method, user, success) VALUES (?, ?, ?, ?)",
            (ts, method, user, int(success)),
        )

    def access_log(self, limit: int) -> list[dict]:
        rows = self._all("SELECT * FROM access_log ORDER BY id DESC LIMIT ?", (limit,))
        return [
            {"ts": r["ts"], "method": r["method"], "user": r["user"], "success": bool(r["success"])}
            for r in rows
        ]

    # lab results
    def add_lab_result(self, ts: float, result: str, target: str, notes: str, author: str) -> int:
        cur = self._run(
            "INSERT INTO lab_results (ts, result, target, notes, author) VALUES (?, ?, ?, ?, ?)",
            (ts, result, target, notes, author),
        )
        return int(cur.lastrowid)

    def lab_results(self, limit: int) -> list[dict]:
        rows = self._all("SELECT * FROM lab_results ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]

    # settings
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        rows = self._all("SELECT value FROM settings WHERE key = ?", (key,))
        return rows[0]["value"] if rows else default

    def set_setting(self, key: str, value: str) -> None:
        self._run(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
