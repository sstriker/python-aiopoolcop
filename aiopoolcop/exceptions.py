"""Exceptions for PoolCop Client API."""

from __future__ import annotations


class PoolCopClientError(Exception):
    """Generic PoolCop Client API exception."""


class PoolCopClientConnectionError(PoolCopClientError):
    """PoolCop Client API connection error."""


class PoolCopClientAuthError(PoolCopClientError):
    """PoolCop Client API authentication error (invalid API key)."""


class PoolCopClientAccessExpiredError(PoolCopClientError):
    """The device's PoolCop cloud access has expired (HTTP 402)."""


class PoolCopClientNotFoundError(PoolCopClientError):
    """PoolCop Client API resource not found."""


class PoolCopClientRateLimitError(PoolCopClientError):
    """PoolCop Client API rate limit exceeded."""

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


# Backwards-compatible aliases for existing integrations
PoolCopCloudError = PoolCopClientError
PoolCopCloudConnectionError = PoolCopClientConnectionError
PoolCopCloudAuthError = PoolCopClientAuthError
PoolCopCloudNotFoundError = PoolCopClientNotFoundError
PoolCopCloudRateLimitError = PoolCopClientRateLimitError
