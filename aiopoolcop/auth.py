"""OAuth2 token management for PoolCop Cloud API."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass
class TokenManager:
    """Manages OAuth2 access tokens with refresh support.

    The token_refresh_callback is called when a 401 is received,
    and should return a new valid access token string.
    """

    token: str
    token_refresh_callback: Callable[[], Awaitable[str]] | None = None

    async def refresh(self) -> str:
        """Refresh the token using the callback.

        Returns the new token.

        Raises:
            RuntimeError: If no refresh callback is configured.
        """
        if self.token_refresh_callback is None:
            msg = "No token refresh callback configured"
            raise RuntimeError(msg)
        self.token = await self.token_refresh_callback()
        return self.token
