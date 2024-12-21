import asyncio
import os
from asyncpg import connect
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    conn = await connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        ssl="require"
    )
    print("Connection successful!")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
