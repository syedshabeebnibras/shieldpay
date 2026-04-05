import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() != "false"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    enabled=_enabled,
)

# Per-route decorators: use @limiter.limit("10/minute") on auth endpoints
# and @limiter.limit("5/minute") on webhook endpoints
# Applied directly in the route handlers via the limiter instance.
AUTH_LIMIT = "10/minute"
WEBHOOK_LIMIT = "5/minute"
