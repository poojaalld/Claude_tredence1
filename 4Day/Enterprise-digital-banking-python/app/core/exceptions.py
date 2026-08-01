"""Domain exceptions + the single place that maps them to HTTP responses.

Mirrors the Java project's common/exception package: domain services raise
ResourceNotFoundException / BadRequestException instead of building HTTP
responses themselves, keeping routers thin.
"""

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ResourceNotFoundException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BadRequestException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ForbiddenException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UnauthorizedException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _error_body(request: Request, status: int, error: str, messages: list[str]) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "error": error,
        "messages": messages,
        "path": request.url.path,
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ResourceNotFoundException)
    async def handle_not_found(request: Request, exc: ResourceNotFoundException):
        return JSONResponse(status_code=404, content=_error_body(request, 404, "Not Found", [exc.message]))

    @app.exception_handler(BadRequestException)
    async def handle_bad_request(request: Request, exc: BadRequestException):
        return JSONResponse(status_code=400, content=_error_body(request, 400, "Bad Request", [exc.message]))

    @app.exception_handler(ForbiddenException)
    async def handle_forbidden(request: Request, exc: ForbiddenException):
        return JSONResponse(status_code=403, content=_error_body(request, 403, "Forbidden", [exc.message]))

    @app.exception_handler(UnauthorizedException)
    async def handle_unauthorized(request: Request, exc: UnauthorizedException):
        return JSONResponse(
            status_code=401,
            content=_error_body(request, 401, "Unauthorized", [exc.message]),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        messages = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        return JSONResponse(status_code=422, content=_error_body(request, 422, "Validation Error", messages))
