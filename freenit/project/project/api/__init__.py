# The Freenit API is built dynamically from the modules listed in
# config.modules (default: ["auth"]). Importing the router here mounts all
# configured modules. Add project-specific routes below if needed.

from freenit.api.router import api

__all__ = ["api"]
