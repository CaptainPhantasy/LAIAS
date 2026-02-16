"""
Agent Generator Service - Main Application

FastAPI service that uses LLMs to generate production-ready
CrewAI agent code from natural language descriptions.

Author: LAIAS Production Team
Version: 1.0.0
"""

# =============================================================================
# CRITICAL: Load .env into os.environ BEFORE importing settings
# =============================================================================
# pydantic-settings loads .env into model fields but does NOT export to os.environ
# LLMProvider uses os.getenv() which requires vars in actual environment
from pathlib import Path
from dotenv import load_dotenv

_CONFIG_DIR = Path(__file__).parent.parent  # app/main.py -> services/agent-generator
_ENV_FILE = _CONFIG_DIR / ".env"
load_dotenv(_ENV_FILE)  # Export .env to os.environ

# Now safe to import settings (which will also read from the now-loaded env)
from app.config import settings

# =============================================================================
# Remaining imports
# =============================================================================
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from time import time
from app import __version__

# =============================================================================
# Logging Configuration
# =============================================================================

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# =============================================================================
# Lifespan Context Manager
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    logger.info(
        "Starting Agent Generator Service",
        version=__version__,
        environment=settings.environment
    )
    # Initialize database
    from app.database import init_db
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
    yield
    # Close database connections
    from app.database import close_db
    await close_db()
    logger.info("Shutting down Agent Generator Service")


# =============================================================================
# Application Factory
# =============================================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="LLM-powered CrewAI agent code generator",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
    )

    # =============================================================================
    # CORS Middleware
    # =============================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # =============================================================================
    # Exception Handlers
    # =============================================================================
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "message": str(exc)}
        )

    # =============================================================================
    # Include Routers
    # =============================================================================
    from app.api.routes.generate import router as generate_router
    from app.api.routes.validate import router as validate_router
    from app.api.routes.health import router as health_router
    from app.api.routes.agents import router as agents_router
    from app.api.routes.tools import router as tools_router
    from app.api.routes.users import router as users_router
    from app.api.routes.teams import router as teams_router
    from app.api.routes.templates import router as templates_router

    app.include_router(generate_router)
    app.include_router(validate_router)
    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(tools_router)
    app.include_router(users_router)
    app.include_router(teams_router)
    app.include_router(templates_router)

    # =============================================================================
    # Root Endpoint
    # =============================================================================
    @app.get("/", status_code=200)
    async def root():
        """Root endpoint with service information."""
        return {
            "service": settings.app_name,
            "version": __version__,
            "status": "running",
            "docs": "/docs" if settings.debug else "disabled"
        }

    return app


# =============================================================================
# Application Instance
# =============================================================================

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
