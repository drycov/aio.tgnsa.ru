from firebase_admin import db
from datetime import datetime, timezone

class AdminLogger:
    @staticmethod
    def log_action(admin_tg_id: int, action: str, target_user_id: int):
        log_ref = db.reference('logs/admin_actions')
        log_ref.push({
            "admin_id": admin_tg_id,
            "action": action,
            "target_user_id": target_user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
