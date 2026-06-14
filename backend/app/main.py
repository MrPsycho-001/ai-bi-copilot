import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.api.router import api_router
from app.db.session import engine
from app.db.base_models import Base

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("aibi_backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI BI Copilot Engine...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
            # Seed a default simulation user for initial development
            await conn.execute(text("""
                INSERT INTO users (id, username, email, hashed_password, created_at)
                VALUES (1, 'dev_user', 'dev@example.com', 'scrypted_placeholder_hash', NOW())
                ON CONFLICT (id) DO NOTHING;
            """))
            
            logger.info("SUCCESS: Connected to Database & Tables Synced successfully!")
    except Exception as e:
        logger.error(f"CRITICAL: Database initialization failed: {e}")
    yield
    logger.info("Shutting down AI BI Copilot Engine...")
    await engine.dispose()

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        lifespan=lifespan
    )

    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    application.include_router(api_router, prefix=settings.API_V1_STR)
    return application

app = create_application()
