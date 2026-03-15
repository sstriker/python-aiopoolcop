"""Exceptions for PoolCop Cloud API client."""

from __future__ import annotations


class PoolCopCloudError(Exception):
    """Generic PoolCop Cloud API exception."""


class PoolCopCloudConnectionError(PoolCopCloudError):
    """PoolCop Cloud API connection error."""


class PoolCopCloudAuthError(PoolCopCloudError):
    """PoolCop Cloud API authentication/authorization error."""


class PoolCopCloudNotFoundError(PoolCopCloudError):
    """PoolCop Cloud API resource not found."""


class PoolCopCloudRateLimitError(PoolCopCloudError):
    """PoolCop Cloud API rate limit exceeded."""

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
