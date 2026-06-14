from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Initialize the async engine connecting to our PostgreSQL container
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10
)

# Factory to spin up isolated database sessions for API requests
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """FastAPI Dependency injector yielding an independent database session."""
    async with AsyncSessionLocal() as session:
        yield session
