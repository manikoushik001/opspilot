import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import get_logger
from app.core.database import async_engine, Base
from app.api.v1.api import api_router

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schemas...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"{settings.PROJECT_NAME} backend started successfully.")
    yield
    logger.info(f"{settings.PROJECT_NAME} backend shutting down...")
    await async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="OpsPilot: AI-powered customer operations SaaS platform for small businesses.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS Configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Structured Request Logging Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = (time.time() - start_time) * 1000
    logger.info(
        f"[{request.method}] {request.url.path} -> {response.status_code} "
        f"({duration:.1f}ms) req_id={request_id}"
    )
    response.headers["X-Request-ID"] = request_id
    return response


# Global Safe Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request.",
            "status_code": 500
        }
    )


# Health Check Endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to OpsPilot API",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health"
    }


# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)
