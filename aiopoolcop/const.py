"""Constants for PoolCop Client API."""

from importlib import metadata
from typing import Final

API_HOST: Final = "client-api.poolcop.net"
API_BASE_PATH: Final = ""
USER_AGENT: Final = f"python-aiopoolcop/{metadata.version(__package__)}"
