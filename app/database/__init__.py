# app/services/__init__.py
from .user_service import (
    save_user as save,
    get_all_users as get_all,
    get_user_by_tg_id as get_by_tg_id,
    get_admin_users as get_admins,
    update_user as update,
    handle_error as handle_err,
    handle_result_not_found as handle_not_found,
)

# Оставляем только алиасы, чтобы упростить доступ к функциям из других модулей
__all__ = [
    'save',
    'get_all',
    'get_by_tg_id',
    'get_admins',
    'update',
    'handle_err',
    'handle_not_found'
]
