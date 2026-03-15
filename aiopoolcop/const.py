"""Constants for PoolCop Cloud API client."""

from importlib import metadata
from typing import Final

API_HOST: Final = "cloud.api.poolcop.net"
API_BASE_PATH: Final = "/v1"
USER_AGENT: Final = f"python-aiopoolcop/{metadata.version(__package__)}"
