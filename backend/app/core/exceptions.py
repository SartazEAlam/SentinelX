"""Custom exceptions for SentinelX."""

class SentinelXError(Exception):
    """Base exception for all custom SentinelX errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(SentinelXError):
    """Resource not found."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND")


class ConflictError(SentinelXError):
    """Resource conflict (e.g., duplicate)."""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, code="CONFLICT")


class ForbiddenError(SentinelXError):
    """Access denied (authenticated but lacking permissions)."""
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, code="FORBIDDEN")


class UnauthorizedError(SentinelXError):
    """Authentication required or failed."""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED")
