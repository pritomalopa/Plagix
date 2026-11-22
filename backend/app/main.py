from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from app.core.config import settings
from app.db.session import get_db
from app.api.auth import router as auth_router
from app.api.evaluations import router as evaluations_router
from app.api.submissions import router as submissions_router
from app.api.similarity import router as similarity_router
from app.api.relevance import router as relevance_router

app = FastAPI(
    title="PLAGIX API",
    description="Academic Answer Evaluation & Integrity Platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include Routers
app.include_router(auth_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(similarity_router, prefix="/api")
app.include_router(relevance_router, prefix="/api")


@app.get("/health/live", tags=["Health"])
def health_live():
    """Liveness probe: returns 200 if API container is running."""
    return {"status": "alive", "environment": settings.app_env}


@app.get("/health/ready", tags=["Health"])
def health_ready(db: Session = Depends(get_db)):
    """
    Readiness probe: checks database connectivity and Redis connection.
    Returns 200 if all backend services are healthy and reachable.
    """
    health_status = {
        "status": "ready",
        "database": "unhealthy",
        "redis": "unhealthy",
    }
    
    # Check Database
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        if r.ping():
            health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"unhealthy: {str(e)}"
    
    # If any core service is unhealthy, return 503
    if health_status["database"] != "healthy" or health_status["redis"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status


@app.get("/", tags=["Root"])
def root():
    """Root endpoint for PLAGIX API."""
    return {
        "product": "PLAGIX",
        "description": "Academic Answer Evaluation & Integrity Platform",
        "version": "0.1.0",
        "docs": "/docs"
    }
