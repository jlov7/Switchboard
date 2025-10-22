#!/usr/bin/env python3
from __future__ import annotations

import asyncio

from switchboard.storage.database import Database, DatabaseConfig


async def main() -> None:
    db = Database(DatabaseConfig.from_env())
    await db.connect()
    await db.ensure_schema()
    await db.disconnect()
    print("Database schema ensured at", db.config.url)


if __name__ == "__main__":
    asyncio.run(main())
