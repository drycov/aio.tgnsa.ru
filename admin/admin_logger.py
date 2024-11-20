"""
This module provides functionality for logging administrative actions
to a Firebase Realtime Database.
"""

from datetime import datetime, timezone
from firebase_admin import db


class AdminLogger:
    """
    A utility class for logging administrative actions to Firebase.
    """

    @staticmethod
    def log_action(admin_tg_id: int, action: str, target_user_id: int):
        """
        Logs an administrative action to the Firebase Realtime Database.

        Args:
            admin_tg_id (int): The Telegram ID of the admin performing the action.
            action (str): A description of the action performed.
            target_user_id (int): The ID of the target user affected by the action.
        """
        log_ref = db.reference('logs/admin_actions')
        log_ref.push({
            "admin_id": admin_tg_id,
            "action": action,
            "target_user_id": target_user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
