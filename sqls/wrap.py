import asyncpg


class SQL_Wrapper:
    def __init__(self, sql: asyncpg.Pool):
        self.sql = sql

    async def fetch(self, query: str, *args, **kwargs):
        async with self.sql.acquire() as conn:
            return await conn.fetch(query, *args, **kwargs)

    async def fetchrow(self, query: str, *args, **kwargs):
        async with self.sql.acquire() as conn:
            return await conn.fetchrow(query, *args, **kwargs)

    async def execute(self, query: str, *args, **kwargs):
        async with self.sql.acquire() as conn:
            return await conn.execute(query, *args, **kwargs)

    async def close(self):
        return  # pool can't be closed lmfao
