from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config.base import get_settings
from app.extensions.db import init_db
from app.modules.admin.routes import router as admin_router
from app.modules.auth.routes import router as auth_router
from app.modules.core.routes import router as core_router
from app.modules.student.routes import router as students_router


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, attempts: int, window_seconds: int) -> None:
        super().__init__(app)
        self.attempts = attempts
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "POST" and request.url.path in {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/google",
        }:
            now = monotonic()
            client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
            key = f"{request.url.path}:{client_ip.split(',')[0].strip()}"
            window_start = now - self.window_seconds
            recent_requests = [
                timestamp for timestamp in self._requests.get(key, []) if timestamp >= window_start
            ]
            if len(recent_requests) >= self.attempts:
                return Response(
                    content='{"detail":"Too many authentication attempts. Try again later."}',
                    media_type="application/json",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": str(self.window_seconds)},
                )
            recent_requests.append(now)
            self._requests[key] = recent_requests

        return await call_next(request)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        AuthRateLimitMiddleware,
        attempts=settings.auth_rate_limit_attempts,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )

    app.include_router(core_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(students_router, prefix="/api/v1")
    return app


app = create_app()
