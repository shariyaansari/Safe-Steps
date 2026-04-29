# Everything related to database connection and session management lives here.
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

load_dotenv()
try:    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/safesteps")
    print(f"Database connection successful. Using DATABASE_URL: {DATABASE_URL}")
except Exception as e:
    print(f"[ERROR] Failed to load DATABASE_URL: {e}")

# create_engine -> blocks the event loop, slower under load, Not ideal for modern APIs 
# Therefore, we use create_async_engine, which is non-blocking and allows for better performance in async applications.
engine = create_async_engine(DATABASE_URL, echo=False)

# a session that is conversation with the database, used to run queries, manage transactions, and interact with the database in an async context. expire_on_commit=False means that after a commit, the session won't automatically expire all instances, allowing you to continue using them without needing to refresh from the database. lazy loading avoided 
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


# THis is dependency injection function, used in FASTAPI routes to get a database session. It creates a new session for each request and ensures that the session is properly closed after the request is completed, preventing connection leaks and ensuring efficient resource management.
async def get_db():
    async with AsyncSessionLocal() as session:
        # Why yield instead of return? Because we want to create a generator function that can be used as a dependency in FastAPI. When FastAPI calls this function, it will execute the code up to the yield statement, providing the session to the route handler. After the route handler is done, FastAPI will continue executing the code after the yield statement, which will automatically close the session when the request is completed. This pattern ensures that each request gets a fresh database session and that resources are properly cleaned up afterward.
        yield session
