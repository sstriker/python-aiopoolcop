"""Tests for OAuth2 token management."""

import pytest

from aiopoolcop.auth import TokenManager


async def test_token_stored():
    """TokenManager stores the initial token."""
    tm = TokenManager(token="abc123")
    assert tm.token == "abc123"


async def test_refresh_without_callback():
    """Refresh raises RuntimeError when no callback is set."""
    tm = TokenManager(token="abc123")
    with pytest.raises(RuntimeError, match="No token refresh callback"):
        await tm.refresh()


async def test_refresh_with_callback():
    """Refresh calls the callback and updates the token."""

    async def _refresh() -> str:
        return "new-token-456"

    tm = TokenManager(token="old-token", token_refresh_callback=_refresh)
    result = await tm.refresh()
    assert result == "new-token-456"
    assert tm.token == "new-token-456"


async def test_refresh_updates_token_in_place():
    """Multiple refreshes always update to the latest token."""
    call_count = 0

    async def _refresh() -> str:
        nonlocal call_count
        call_count += 1
        return f"token-v{call_count}"

    tm = TokenManager(token="initial", token_refresh_callback=_refresh)
    await tm.refresh()
    assert tm.token == "token-v1"
    await tm.refresh()
    assert tm.token == "token-v2"
