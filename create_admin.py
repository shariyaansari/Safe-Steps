import asyncio
import uuid
from core.database import AsyncSessionLocal, engine, Base
from core.security import get_password_hash
from models import User, UserRole  # this import registers all models with Base

async def create_admin():
    # create all tables first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] Tables created")

    async with AsyncSessionLocal() as db:
        admin = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@safesteps.com",
            password_hash=get_password_hash("changeme123"),
            role=UserRole.admin
        )
        db.add(admin)
        await db.commit()
        print("Admin created: admin / changeme123")

asyncio.run(create_admin())