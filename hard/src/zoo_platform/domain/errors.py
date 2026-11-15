"""Errors the domain raises. The API layer maps each one to an HTTP status."""

from __future__ import annotations


class ZooError(Exception):
    code = "zoo_error"


class NotFound(ZooError):
    code = "not_found"


class Conflict(ZooError):
    code = "conflict"


class InvalidRequest(ZooError):
    code = "invalid_request"


class Unauthorized(ZooError):
    code = "unauthorized"


class Forbidden(ZooError):
    code = "forbidden"


class ProviderError(ZooError):
    code = "provider_error"


class ProviderUnavailable(ProviderError):
    """Transient: timeout, overload, 5xx from the model provider."""

    code = "provider_unavailable"


class ProviderRejected(ProviderError):
    """Permanent: the provider refused this request."""

    code = "provider_rejected"


class CrewBusy(ZooError):
    """Transient: the cleaning crew cannot take the job right now."""

    code = "crew_busy"
