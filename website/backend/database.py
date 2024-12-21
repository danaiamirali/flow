from asyncpg import create_pool, Pool
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

async def execute_sql_file(file_path: str):
    """Execute the SQL statements in the given file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    
    async with Database.get_connection() as conn:
        with open(file_path, "r") as sql_file:
            sql_script = sql_file.read()
        await conn.execute(sql_script)

class Database:
    _pool: Pool = None

    @classmethod
    async def init_pool(cls):
        """Initialize the connection pool."""
        cls._pool = await create_pool(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            ssl="require",
            min_size=1,  # Minimum number of connections in the pool
            max_size=10  # Maximum number of connections in the pool
        )

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Async context manager for pooled connections."""
        async with cls._pool.acquire() as conn:
            yield conn
