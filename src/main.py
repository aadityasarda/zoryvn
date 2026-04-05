import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.config import get_settings
from src.database import init_db
from src.utils.errors import AppError
from src.routers import auth_router, users_router, records_router, dashboard_router

settings = get_settings()
logger = logging.getLogger("finance_api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Finance Dashboard API...")
    await init_db()
    logger.info("Database initialized")

    await auto_seed()

    yield
    logger.info("Shutting down Finance Dashboard API...")


async def auto_seed():
    from sqlalchemy import select, func
    from src.database import async_session
    from src.models.user import User

    async with async_session() as session:
        count = await session.execute(select(func.count(User.id)))
        if count.scalar() > 0:
            logger.info("Database already has data — skipping seed")
            return

    from seed import seed_database
    logger.info("Empty database detected — seeding sample data...")
    await seed_database()
    logger.info("Sample data seeded successfully")



app = FastAPI(
    title="Finance Dashboard API",
    description=(
        "A production-quality backend for managing financial records, "
        "role-based access control, and dashboard analytics.\n\n"
        "## Roles\n"
        "- **Viewer**: Read-only access to financial records\n"
        "- **Analyst**: Read access + dashboard analytics\n"
        "- **Admin**: Full CRUD + user management\n\n"
        "## Authentication\n"
        "1. Register via `POST /api/auth/register`\n"
        "2. Login via `POST /api/auth/login` to get a JWT token\n"
        "3. Use the token: `Authorization: Bearer <token>`"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)"
    )
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )



app.include_router(auth_router)
app.include_router(users_router)
app.include_router(records_router)
app.include_router(dashboard_router)




@app.get("/", tags=["Health"], summary="Health check")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Detailed health check")
async def detailed_health():
    from src.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status,
        "app": settings.APP_NAME,
    }
