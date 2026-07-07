from __future__ import annotations

import json
import math
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable

import psycopg2
from psycopg2.extras import RealDictCursor


class _SafeJsonEncoder(json.JSONEncoder):
    """Encodes NaN/Inf floats as null and datetime objects as ISO strings."""

    def default(self, obj: Any) -> Any:  # type: ignore[override]
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

    def iterencode(self, obj: Any, _one_shot: bool = False):  # type: ignore[override]
        # Patch the underlying encoder to emit null for NaN/Inf
        return super().iterencode(_replace_nan(obj), _one_shot)


def _replace_nan(obj: Any) -> Any:
    """Recursively replace NaN/Inf floats with None so they serialise as JSON null."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _replace_nan(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_replace_nan(v) for v in obj]
    return obj


def _safe_dumps(obj: Any) -> str:
    """json.dumps with NaN-safe encoding."""
    return json.dumps(_replace_nan(obj), cls=_SafeJsonEncoder)


@dataclass(slots=True)
class DatabaseService:
    database_url: str

    @contextmanager
    def connection(self):
        connection = psycopg2.connect(
            self.database_url,
            connect_timeout=30,
            keepalives=1,
            keepalives_idle=10,
            keepalives_interval=5,
            keepalives_count=3,
        )
        try:
            yield connection
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                connection.close()
            except Exception:
                pass

    def fetch_all(self, query: str, parameters: Iterable[Any] | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, tuple(parameters or ()))
                return list(cursor.fetchall())

    def fetch_one(self, query: str, parameters: Iterable[Any] | None = None) -> dict[str, Any] | None:
        with self.connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, tuple(parameters or ()))
                return cursor.fetchone()

    def execute(self, query: str, parameters: Iterable[Any] | None = None) -> None:
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(parameters or ()))

    def fetch_latest_upload(self) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            select id, file_name, domain_name, confidence, row_count, summary_json, created_at
            from smartbi_uploads
            order by created_at desc
            limit 1
            """
        )

    def fetch_upload_by_id(self, upload_id: int) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            select id, file_name, domain_name, confidence, row_count, summary_json, created_at
            from smartbi_uploads
            where id = %s
            """,
            (upload_id,),
        )

    def fetch_upload_rows(self, upload_id: int) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            select row_data
            from smartbi_clean_rows
            where upload_id = %s
            order by row_number
            """,
            (upload_id,),
        )
        return [row["row_data"] for row in rows]

    def fetch_upload_dataset(self, upload_id: int | None = None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        upload = self.fetch_upload_by_id(upload_id) if upload_id is not None else self.fetch_latest_upload()
        if upload is None:
            return None, []
        return upload, self.fetch_upload_rows(int(upload["id"]))

    def insert_upload(self, *, file_name: str, domain_name: str, confidence: float, row_count: int, summary: dict[str, Any], user_id: int | None = None) -> int:
        query = """
            insert into smartbi_uploads (file_name, domain_name, confidence, row_count, summary_json, user_id)
            values (%s, %s, %s, %s, %s::jsonb, %s)
            returning id
        """
        row = self.fetch_one(query, (file_name, domain_name, confidence, row_count, _safe_dumps(summary), user_id))
        assert row is not None
        return int(row["id"])

    def insert_rows(self, upload_id: int, records: list[dict[str, Any]]) -> None:
        if not records:
            return

        query = """
            insert into smartbi_clean_rows (upload_id, row_number, row_data)
            values (%s, %s, %s::jsonb)
        """
        # Use executemany in a single connection for maximum speed.
        # Neon SSL connection setup is ~300ms, so multiple connections was
        # adding significant latency for large files.
        params = [
            (upload_id, index, _safe_dumps(record))
            for index, record in enumerate(records, start=1)
        ]
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(query, params)
