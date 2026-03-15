"""Tests for the exception hierarchy."""

from aiopoolcop import (
    PoolCopCloudAuthError,
    PoolCopCloudConnectionError,
    PoolCopCloudError,
    PoolCopCloudNotFoundError,
    PoolCopCloudRateLimitError,
)


def test_base_exception():
    """All custom exceptions inherit from PoolCopCloudError."""
    assert issubclass(PoolCopCloudConnectionError, PoolCopCloudError)
    assert issubclass(PoolCopCloudAuthError, PoolCopCloudError)
    assert issubclass(PoolCopCloudNotFoundError, PoolCopCloudError)
    assert issubclass(PoolCopCloudRateLimitError, PoolCopCloudError)


def test_base_inherits_from_exception():
    """PoolCopCloudError inherits from Exception."""
    assert issubclass(PoolCopCloudError, Exception)


def test_rate_limit_retry_after():
    """PoolCopCloudRateLimitError stores retry_after."""
    exc = PoolCopCloudRateLimitError("rate limited", retry_after=60)
    assert str(exc) == "rate limited"
    assert exc.retry_after == 60


def test_rate_limit_no_retry_after():
    """PoolCopCloudRateLimitError retry_after defaults to None."""
    exc = PoolCopCloudRateLimitError("rate limited")
    assert exc.retry_after is None


def test_exception_message():
    """All exceptions carry their message."""
    for exc_cls in (
        PoolCopCloudError,
        PoolCopCloudConnectionError,
        PoolCopCloudAuthError,
        PoolCopCloudNotFoundError,
    ):
        exc = exc_cls("test message")
        assert str(exc) == "test message"
