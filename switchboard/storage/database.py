from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, cast

import aiosqlite
import asyncpg


@dataclass
class DatabaseConfig:
    url: str

    @staticmethod
    def from_env() -> DatabaseConfig:
        url = os.getenv("SWITCHBOARD_DATABASE_URL")
        if not url:
            # Default to sqlite file for developer ergonomics
            url = "sqlite+aiosqlite:///data/switchboard.db"
        return DatabaseConfig(url=url)

    @property
    def dialect(self) -> str:
        if self.url.startswith("postgresql") or self.url.startswith("postgres"):
            return "postgres"
        if self.url.startswith("sqlite"):
            return "sqlite"
        raise ValueError(f"Unsupported database URL: {self.url}")


class Database:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or DatabaseConfig.from_env()
        self._sqlite: aiosqlite.Connection | None = None
        self._postgres: asyncpg.Connection | None = None

    async def connect(self) -> None:
        if self.config.dialect == "sqlite":
            path = self.config.url.replace("sqlite+aiosqlite:///", "")
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            self._sqlite = await aiosqlite.connect(path)
            await self._sqlite.execute("PRAGMA journal_mode=WAL;")
            await self._sqlite.execute("PRAGMA foreign_keys=ON;")
        elif self.config.dialect == "postgres":
            dsn = self.config.url.replace("+asyncpg", "")
            self._postgres = await asyncpg.connect(dsn)
        else:
            raise ValueError(f"Unsupported dialect: {self.config.dialect}")

    async def disconnect(self) -> None:
        if self._sqlite:
            await self._sqlite.close()
            self._sqlite = None
        if self._postgres:
            await self._postgres.close()
            self._postgres = None

    async def execute(self, query: str, *params: Any) -> None:
        if self.config.dialect == "sqlite":
            assert self._sqlite is not None, "SQLite connection not initialized"
            await self._sqlite.execute(query, params)
            await self._sqlite.commit()
        else:
            assert self._postgres is not None, "Postgres connection not initialized"
            await self._postgres.execute(query, *params)

    async def fetchall(self, query: str, *params: Any) -> list[dict[str, Any]]:
        if self.config.dialect == "sqlite":
            assert self._sqlite is not None, "SQLite connection not initialized"
            self._sqlite.row_factory = aiosqlite.Row
            cursor = await self._sqlite.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        else:
            assert self._postgres is not None, "Postgres connection not initialized"
            records = await self._postgres.fetch(query, *params)
            return [dict(record) for record in records]

    async def fetchone(self, query: str, *params: Any) -> dict[str, Any] | None:
        rows = await self.fetchall(query, *params)
        return rows[0] if rows else None

    async def ensure_schema(self) -> None:
        approvals_sql = """
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                request_json TEXT NOT NULL,
                policy_json TEXT NOT NULL,
                adapter TEXT NOT NULL,
                status TEXT NOT NULL,
                decided_by TEXT,
                decided_at TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        await self.execute(approvals_sql)

        audit_sql = """
            CREATE TABLE IF NOT EXISTS audit_cache (
                event_id TEXT PRIMARY KEY,
                approval_id TEXT,
                record_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        await self.execute(audit_sql)

    @staticmethod
    def dumps(data: dict[str, Any]) -> str:
        return json.dumps(data, default=str)

    @staticmethod
    def loads(payload: str) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(payload))
