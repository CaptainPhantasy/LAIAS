"""
Custom exceptions for Agent Generator Service.

Provides domain-specific exceptions for better error handling
and more meaningful error messages to clients.
"""

from typing import Optional


class AgentGeneratorException(Exception):
    """Base exception for Agent Generator Service."""

    def __init__(
        self,
        message: str,
        detail: Optional[str] = None,
        error_code: str = "AGENT_GENERATOR_ERROR"
    ):
        self.message = message
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.message)


class CodeValidationError(AgentGeneratorException):
    """Raised when code validation fails."""

    def __init__(
        self,
        message: str,
        errors: list,
        warnings: list = None
    ):
        self.errors = errors
        self.warnings = warnings or []
        detail = f"Errors: {errors}; Warnings: {self.warnings}"
        super().__init__(message, detail=detail, error_code="CODE_VALIDATION_ERROR")


class LLMServiceException(AgentGeneratorException):
    """Raised when LLM service fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        self.provider = provider
        self.original_error = original_error
        detail = f"Provider: {provider}" if provider else None
        if original_error:
            detail = f"{detail}: {str(original_error)}" if detail else str(original_error)
        super().__init__(message, detail=detail, error_code="LLM_SERVICE_ERROR")


class DatabaseException(AgentGeneratorException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        self.query = query
        self.original_error = original_error
        detail = f"Query: {query}" if query else None
        if original_error:
            detail = f"{detail}: {str(original_error)}" if detail else str(original_error)
        super().__init__(message, detail=detail, error_code="DATABASE_ERROR")


class CacheException(AgentGeneratorException):
    """Raised when cache operations fail."""

    def __init__(
        self,
        message: str,
        key: Optional[str] = None
    ):
        self.key = key
        detail = f"Key: {key}" if key else None
        super().__init__(message, detail=detail, error_code="CACHE_ERROR")


class ValidationException(AgentGeneratorException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        self.field = field
        self.value = value
        detail = f"Field: {field}, Value: {value}" if field else None
        super().__init__(message, detail=detail, error_code="VALIDATION_ERROR")


class RateLimitException(AgentGeneratorException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        self.retry_after = retry_after
        detail = f"Retry after: {retry_after}s" if retry_after else None
        super().__init__(message, detail=detail, error_code="RATE_LIMIT_ERROR")


class ConfigurationException(AgentGeneratorException):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        setting: Optional[str] = None
    ):
        self.setting = setting
        detail = f"Setting: {setting}" if setting else None
        super().__init__(message, detail=detail, error_code="CONFIGURATION_ERROR")
