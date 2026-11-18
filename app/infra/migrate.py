"""For first-time local demo only. Use reviewed migrations in production."""
import asyncio
from app.core.settings import get_settings
from app.infra.database import Base, Database

async def main():
    db = Database(get_settings().database_url)
    try:
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
