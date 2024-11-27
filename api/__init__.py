"""
This module initializes the admin package.

It provides the following functionality:
- AdminLogger for logging.
- AdminService for administrative operations.
- Functions to run and stop the server.
"""


from api.app import API

__version__ = "0.1.0"
__all__ = ["API"]

