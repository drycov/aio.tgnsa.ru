from .advanced_menu import advanced_keyboard
from .device_menu import device_keyboard
from .keyboards import on_enter_keyboard, in_back_keyboard, send_contact_keyboard, verify_user_keyboard, priority_kb, \
    on_back_keyboard
from .main_menu import generate_main_keyboard, confirm_keyboard, confirm_keyboard_inl, admin_menu, system_info_menu
from .task_menu import task_keyboard

__all__ = ["on_enter_keyboard", "in_back_keyboard",
           "send_contact_keyboard", "verify_user_keyboard",
           "generate_main_keyboard", "admin_menu",
           "device_keyboard", "advanced_keyboard", "confirm_keyboard", "confirm_keyboard_inl", "priority_kb",
           "on_back_keyboard",
           "task_keyboard", "system_info_menu"]
