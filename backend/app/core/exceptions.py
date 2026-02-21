"""Custom exception hierarchy for Synapse.

These exceptions are raised in service/domain code and caught by
FastAPI exception handlers (registered in main.py) which convert
them to proper HTTP responses. This keeps business logic free of
HTTP concepts.

Hierarchy:
    SynapseError (base)
    ├── NotFoundError          → 404
    ├── ValidationError        → 422
    ├── ConflictError          → 409
    ├── ProviderError          → 502
    │   ├── ProviderAuthError  → 401
    │   └── ProviderRateLimitError → 429
    └── ExecutionError         → 500
"""


class SynapseError(Exception):
    """Base exception for all Synapse errors.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code (e.g., "WORKFLOW_NOT_FOUND").
    """

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(SynapseError):
    """Resource not found (HTTP 404)."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            code=f"{resource.upper()}_NOT_FOUND",
        )


class ValidationError(SynapseError):
    """Invalid input data (HTTP 422)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR")


class ConflictError(SynapseError):
    """Resource conflict, e.g., duplicate name (HTTP 409)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="CONFLICT")


class ProviderError(SynapseError):
    """Error communicating with an LLM provider (HTTP 502)."""

    def __init__(self, provider: str, message: str) -> None:
        super().__init__(
            message=f"Provider '{provider}' error: {message}",
            code="PROVIDER_ERROR",
        )


class ProviderAuthError(ProviderError):
    """Invalid or missing API key for a provider (HTTP 401)."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            provider=provider,
            message="Invalid or missing API key",
        )
        self.code = "PROVIDER_AUTH_ERROR"


class ProviderRateLimitError(ProviderError):
    """Rate limit exceeded for a provider (HTTP 429)."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            provider=provider,
            message="Rate limit exceeded",
        )
        self.code = "PROVIDER_RATE_LIMIT"


class ExecutionError(SynapseError):
    """Workflow execution failed (HTTP 500)."""

    def __init__(self, message: str, agent_id: str | None = None) -> None:
        self.agent_id = agent_id
        super().__init__(message=message, code="EXECUTION_ERROR")