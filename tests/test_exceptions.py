"""Tests for the exception hierarchy."""

from aiopoolcop import (
    PoolCopClientAuthError,
    PoolCopClientConnectionError,
    PoolCopClientError,
    PoolCopClientNotFoundError,
    PoolCopClientRateLimitError,
)


def test_base_exception():
    """All custom exceptions inherit from PoolCopClientError."""
    assert issubclass(PoolCopClientConnectionError, PoolCopClientError)
    assert issubclass(PoolCopClientAuthError, PoolCopClientError)
    assert issubclass(PoolCopClientNotFoundError, PoolCopClientError)
    assert issubclass(PoolCopClientRateLimitError, PoolCopClientError)


def test_base_inherits_from_exception():
    """PoolCopClientError inherits from Exception."""
    assert issubclass(PoolCopClientError, Exception)


def test_rate_limit_retry_after():
    """PoolCopClientRateLimitError stores retry_after."""
    exc = PoolCopClientRateLimitError("rate limited", retry_after=60)
    assert str(exc) == "rate limited"
    assert exc.retry_after == 60


def test_rate_limit_no_retry_after():
    """PoolCopClientRateLimitError retry_after defaults to None."""
    exc = PoolCopClientRateLimitError("rate limited")
    assert exc.retry_after is None


def test_exception_message():
    """All exceptions carry their message."""
    for exc_cls in (
        PoolCopClientError,
        PoolCopClientConnectionError,
        PoolCopClientAuthError,
        PoolCopClientNotFoundError,
    ):
        exc = exc_cls("test message")
        assert str(exc) == "test message"
