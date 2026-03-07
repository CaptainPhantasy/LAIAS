import structlog
from fastapi import Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

logger = structlog.get_logger()


def _is_auth_enabled() -> bool:
    return len(settings.API_KEYS) > 0


def is_api_key_valid(api_key: str | None) -> bool:
    if not _is_auth_enabled():
        return True
    return bool(api_key and api_key in settings.API_KEYS)


def _extract_api_key(request: Request) -> str | None:
    api_key = request.headers.get(settings.API_KEY_HEADER)
    if api_key:
        return api_key

    return None


async def verify_api_key(
    api_key: str | None = Header(default=None, alias=settings.API_KEY_HEADER),
) -> None:
    if is_api_key_valid(api_key):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error_code": "UNAUTHORIZED",
            "message": "Invalid or missing API key",
        },
    )


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if not _is_auth_enabled():
            return await call_next(request)

        if path == "/health" or path.startswith("/health/") or path.startswith("/api/health"):
            return await call_next(request)

        api_key = _extract_api_key(request)
        if is_api_key_valid(api_key):
            return await call_next(request)

        logger.warning("Unauthorized request", path=path, method=request.method)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error_code": "UNAUTHORIZED",
                "message": "Invalid or missing API key",
            },
        )
