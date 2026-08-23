import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_access_token
from app.db.database import Sessionlocal
from app.models.audit import AuditLog

# Endpoints that don't need to be audited (health checks, docs, static assets).
_EXCLUDED_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/favicon.ico")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Records who did what, on which endpoint, and when - satisfying the
    "User activity / Security logs" requirement of the Audit module without
    having to sprinkle logging calls through every existing service/router.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(_EXCLUDED_PREFIXES):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        user_id = None
        user_role = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            payload = decode_access_token(auth_header.split(" ", 1)[1])
            if payload:
                user_id = payload.get("sub")
                user_role = payload.get("role")

        db = Sessionlocal()
        try:
            db.add(
                AuditLog(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    user_id=int(user_id) if user_id else None,
                    user_role=user_role,
                    client_ip=request.client.host if request.client else None,
                    duration_ms=duration_ms,
                )
            )
            db.commit()
        except Exception:
            # Auditing must never break the actual request/response cycle.
            db.rollback()
        finally:
            db.close()

        return response
