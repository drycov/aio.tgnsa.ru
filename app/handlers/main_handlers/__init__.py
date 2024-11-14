from .main_callback import router as main_callback_router
from .main_commands import router as main_commands_router
from .registration_handler import router as registration_router

__all__ = ["registration_router", "main_commands_router", "main_callback_router"]
