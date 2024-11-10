from .advanced_menu import advanced_keyboard
from .device_menu import device_keyboard
from .keyboards import on_enter_keyboard, in_back_keyboard, send_contact_keyboard, verify_user_keyboard, priority_kb
from .main_menu import admin_keyboard, main_keyboard, confirm_keyboard, confirm_keyboard_inl

__all__ = ["on_enter_keyboard", "in_back_keyboard",
           "send_contact_keyboard", "verify_user_keyboard",
           "admin_keyboard", "main_keyboard",
           "device_keyboard", "advanced_keyboard", "confirm_keyboard", "confirm_keyboard_inl", "priority_kb"]
