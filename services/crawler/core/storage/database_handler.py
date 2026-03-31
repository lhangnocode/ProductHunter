from __future__ import annotations

import os
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Optional, Sequence
from urllib.parse import urlparse


class DatabaseHandler:
    """Lightweight DB handler with connect + query helpers."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        self._load_env_file()
        self.db_url = db_url or self._build_db_url()
        self._conn = None

    def connect(self) -> Any:
        """Open a database connection based on db_url.

        Supported:
        - sqlite:///path/to.db or sqlite:///:memory:
        - postgresql://... (requires psycopg2)
        """
        parsed = urlparse(self.db_url)
        scheme = parsed.scheme.lower()

        if scheme in {"sqlite", ""}:
            path = parsed.path or ":memory:"
            if path.startswith("/") and path != "/:memory:":
                path = path[1:]
            self._conn = sqlite3.connect(path)
            self._conn.row_factory = sqlite3.Row
            return self._conn

        if scheme in {"postgres", "postgresql"}:
            try:
                import psycopg2
            except Exception as exc:  # pragma: no cover
                raise RuntimeError("psycopg2 is required for PostgreSQL connections") from exc
            self._conn = psycopg2.connect(self.db_url)
            return self._conn

        raise ValueError(f"Unsupported database scheme: {scheme}")

    def query(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        """Execute a query and return rows or rowcount.

        - For SELECT, returns List[dict]
        - For non-SELECT, returns affected row count
        """
        conn = self._conn or self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params or [])

        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

        conn.commit()
        return cursor.rowcount

    def executemany(self, sql: str, params_list: Iterable[Sequence[Any]]) -> int:
        conn = self._conn or self.connect()
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        conn.commit()
        return cursor.rowcount

    def close_connection(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _load_env_file(self) -> None:
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if not env_path.exists():
            return

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    def _build_db_url(self) -> str:
        env_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        if env_url:
            return env_url

        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD", "")
        db_name = os.getenv("POSTGRES_DB")

        if host and user and db_name:
            if password:
                return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
            return f"postgresql://{user}@{host}:{port}/{db_name}"

        return "sqlite:///crawler.db"
