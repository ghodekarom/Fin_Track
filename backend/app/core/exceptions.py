from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class FinTrackException(Exception):
    """Base exception for all FinTrack domain errors."""

    def __init__(self, message: str, code: str = "BAD_REQUEST", field: str | None = None):
        self.message = message
        self.code = code
        self.field = field
        super().__init__(message)


class NotFoundException(FinTrackException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, code="NOT_FOUND", field=field)


class ConflictException(FinTrackException):
    """Raised when a resource operation conflicts with another constraint."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, code="CONFLICT", field=field)


class ValidationException(FinTrackException):
    """Raised when request payload fails business logic validation."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, code="VALIDATION_ERROR", field=field)


class UnauthorizedException(FinTrackException):
    """Raised when authentication fails or token is invalid/expired."""

    def __init__(self, message: str = "Could not validate credentials", field: str | None = None):
        super().__init__(message, code="UNAUTHORIZED", field=field)


class ForbiddenException(FinTrackException):
    """Raised when an authenticated user attempts to access another user's resource."""

    def __init__(self, message: str = "You do not have permission to access this resource", field: str | None = None):
        super().__init__(message, code="FORBIDDEN", field=field)


def setup_exception_handlers(app: FastAPI) -> None:
    """Mount exceptions handlers on the FastAPI application."""

    @app.exception_handler(FinTrackException)
    async def fintrack_exception_handler(
        request: Request, exc: FinTrackException
    ) -> JSONResponse:
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, NotFoundException):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, ConflictException):
            status_code = status.HTTP_409_CONFLICT
        elif isinstance(exc, ValidationException):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, UnauthorizedException):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, ForbiddenException):
            status_code = status.HTTP_403_FORBIDDEN

        headers = {}
        if isinstance(exc, UnauthorizedException):
            headers["WWW-Authenticate"] = "Bearer"

        return JSONResponse(
            status_code=status_code,
            headers=headers,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "field": exc.field,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        if errors:
            err = errors[0]
            loc = err.get("loc", [])
            field = str(loc[-1]) if len(loc) > 1 else (str(loc[0]) if loc else None)
            if field == "body":
                field = None
            msg = err.get("msg", "Validation error")
            if msg.startswith("Value error, "):
                msg = msg[13:]

            if field and msg.lower() == "field required":
                message = f"Missing required field: '{field}'"
            elif field:
                message = f"{field.replace('_', ' ').capitalize()}: {msg}"
            else:
                message = msg
        else:
            field = None
            message = "Validation error"

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": message,
                    "field": field,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "field": None,
                }
            },
        )
