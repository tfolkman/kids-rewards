import json
from enum import Enum
from typing import Any, Optional

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware


class ErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INSUFFICIENT_POINTS = "INSUFFICIENT_POINTS"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    NOT_PENDING = "NOT_PENDING"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[ApiError] = None
    meta: Optional[dict] = None


SKIP_PATHS = {"/token", "/health", "/", "/hello", "/openapi.json", "/docs", "/redoc"}


def _should_wrap(path: str) -> bool:
    if path in SKIP_PATHS:
        return False
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return False
    return True


def _status_to_error_code(status_code: int, detail: str = "") -> str:
    detail_lower = detail.lower()
    if status_code == 401:
        return ErrorCode.INVALID_CREDENTIALS
    if status_code == 403:
        return ErrorCode.FORBIDDEN
    if status_code == 404:
        return ErrorCode.NOT_FOUND
    if status_code == 422:
        return ErrorCode.VALIDATION_ERROR
    if status_code == 400:
        if "already" in detail_lower:
            return ErrorCode.ALREADY_EXISTS
        if (
            "not enough points" in detail_lower
            or "insufficient" in detail_lower
            or "no longer has enough" in detail_lower
        ):
            return ErrorCode.INSUFFICIENT_POINTS
        if "not pending" in detail_lower:
            return ErrorCode.NOT_PENDING
        return ErrorCode.BAD_REQUEST
    return ErrorCode.INTERNAL_ERROR


def error_response(status_code: int, code: str, message: str, details: dict = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            ApiResponse(
                success=False,
                error=ApiError(code=code, message=message, details=details),
            )
        ),
    )


def success_response(data: Any, status_code: int = 200, meta: dict = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(ApiResponse(success=True, data=data, meta=meta)),
    )


def register_exception_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        if not _should_wrap(request.url.path):
            return JSONResponse(status_code=422, content={"detail": exc.errors()})
        errors = exc.errors()
        fields = [
            {"field": ".".join(str(loc) for loc in e.get("loc", [])), "message": e.get("msg", "")} for e in errors
        ]
        return error_response(
            status_code=422,
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation error",
            details={"fields": fields},
        )


def _wrap_error(original: dict, status_code: int) -> JSONResponse:
    detail = original.get("detail", "")
    if isinstance(detail, list):
        detail = str(detail)
    code = _status_to_error_code(status_code, detail)
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            ApiResponse(
                success=False,
                error=ApiError(code=code, message=detail if detail else "An error occurred"),
            )
        ),
    )


def _wrap_success(original: Any, status_code: int) -> JSONResponse:
    meta = {}
    if isinstance(original, list):
        meta["count"] = len(original)
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(ApiResponse(success=True, data=original, meta=meta if meta else None)),
    )


class EnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not _should_wrap(request.url.path):
            return await call_next(request)

        response = await call_next(request)

        if response.status_code == 204:
            return JSONResponse(
                status_code=200,
                content=jsonable_encoder(ApiResponse(success=True, data=None)),
            )

        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk.encode("utf-8") if isinstance(chunk, str) else chunk

        try:
            original = json.loads(body_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return response

        if isinstance(original, dict) and "success" in original:
            return JSONResponse(status_code=response.status_code, content=original)

        if response.status_code >= 400:
            if isinstance(original, dict):
                return _wrap_error(original, response.status_code)
            return _wrap_error({}, response.status_code)

        return _wrap_success(original, response.status_code)
