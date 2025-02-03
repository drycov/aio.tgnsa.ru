from typing import Optional, List
from firebase_admin import db
import logging

# Настроим логирование для отслеживания ошибок
logger = logging.getLogger(__name__)

class Shift:
    def __init__(self, date: str, start_time: str, end_time: str, shift_type: str, assigned_to: int, status: str = "planned"):
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.shift_type = shift_type
        self.assigned_to = assigned_to
        self.status = status

    def to_dict(self):
        """
        Преобразует объект Shift в словарь для сохранения в базе данных.
        """
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
        """
        Добавляет смену в базу данных.

        :param shift_data: Данные смены.
        :return: Объект Shift, если добавление прошло успешно, иначе None.
        """
        try:
            # Проверка данных
            if not cls._validate_shift_data(shift_data):
                logger.error(f"Invalid shift data: {shift_data}")
                return None

            shift_ref = db.reference(f'shifts/{shift_data["date"]}_{shift_data["assigned_to"]}')
            shift_ref.set(shift_data)
            logger.info(f"Shift for {shift_data['assigned_to']} on {shift_data['date']} added successfully.")
            return cls(**shift_data)
        except Exception as e:
            logger.error(f"Error adding shift: {e}")
            return None

    @classmethod
    def get_shifts_by_user(cls, user_id: int) -> List["Shift"]:
        """
        Получает все смены, назначенные пользователю.
        """
        try:
            shifts_ref = db.reference('shifts')
            shifts_snapshot = shifts_ref.order_by_child("assigned_to").equal_to(user_id).get()
            if shifts_snapshot:
                return [cls(**shift) for shift in shifts_snapshot.values()]
            else:
                logger.info(f"No shifts found for user {user_id}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving shifts for user {user_id}: {e}")
            return []

    @classmethod
    def update_shift_status(cls, shift_id: str, new_status: str) -> bool:
        """
        Обновляет статус смены.

        :param shift_id: Идентификатор смены.
        :param new_status: Новый статус смены.
        :return: True, если обновление прошло успешно, иначе False.
        """
        try:
            shift_ref = db.reference(f'shifts/{shift_id}')
            shift_ref.update({"status": new_status})
            logger.info(f"Shift {shift_id} status updated to {new_status}.")
            return True
        except Exception as e:
            logger.error(f"Error updating shift {shift_id}: {e}")
            return False

    @staticmethod
    def _validate_shift_data(shift_data: dict) -> bool:
        """
        Валидация данных смены.
        """
        required_fields = ["date", "start_time", "end_time", "shift_type", "assigned_to"]
        for field in required_fields:
            if field not in shift_data or not shift_data[field]:
                logger.error(f"Missing or invalid field: {field}")
                return False
        return True
