from datetime import datetime
from typing import Optional, List
from firebase_admin import db

class Shift:
    def __init__(self, date: str, start_time: str, end_time: str, shift_type: str, assigned_to: int, status: str = "planned"):
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.shift_type = shift_type
        self.assigned_to = assigned_to
        self.status = status

    def to_dict(self):
        return {
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "shift_type": self.shift_type,
            "assigned_to": self.assigned_to,
            "status": self.status,
        }

    @classmethod
    def add_shift(cls, shift_data: dict) -> Optional["Shift"]:
        shift_ref = db.reference(f'shifts/{shift_data["date"]}_{shift_data["assigned_to"]}')
        shift_ref.set(shift_data)
        return cls(**shift_data)

    @classmethod
    def get_shifts_by_user(cls, user_id: int) -> List[dict]:
        shifts_ref = db.reference('shifts')
        shifts_snapshot = shifts_ref.order_by_child("assigned_to").equal_to(user_id).get()
        return [shift for shift in shifts_snapshot.values()] if shifts_snapshot else []

    @classmethod
    def update_shift_status(cls, shift_id: str, new_status: str) -> bool:
        shift_ref = db.reference(f'shifts/{shift_id}')
        shift_ref.update({"status": new_status})
        return True
