from .admin_callback import router as admin_callback_router
from .admin_commands import router as admin_router

__all__ = ["admin_router", "admin_callback_router"]
