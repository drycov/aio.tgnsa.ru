from datetime import datetime
from enum import Enum
from typing import Optional, List

from firebase_admin import db
from pydantic import BaseModel, ValidationError, ConfigDict

from bot.constants import Symbols, PriorityMessages
from bot.utils.logger_instance import app_logger


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def from_str(cls, value: str) -> "PriorityLevel":
        return cls(value.lower())

    @staticmethod
    def get_priority_level(priority_str: str) -> Optional[str]:
        """
        Возвращает уровень приоритета с иконкой и сообщением.
        """
        try:
            priority = PriorityLevel.from_str(priority_str)
            return f"{priority.get_icon()} {priority.get_message()}"
        except ValueError:
            return None

    def get_icon(self) -> str:
        icons = {
            PriorityLevel.LOW: Symbols.INDICATOR_GREEN.value,
            PriorityLevel.MEDIUM: Symbols.INDICATOR_YELLOW.value,
            PriorityLevel.HIGH: Symbols.INDICATOR_RED.value,
        }
        return icons.get(self, Symbols.INDICATOR_GREEN.value)

    def get_message(self) -> str:
        messages = {
            PriorityLevel.LOW: PriorityMessages.PRIORITY_LOW.value,
            PriorityLevel.MEDIUM: PriorityMessages.PRIORITY_MEDIUM.value,
            PriorityLevel.HIGH: PriorityMessages.PRIORITY_HIGH.value,
        }
        return messages.get(self, PriorityMessages.PRIORITY_LOW.value)


class Task(BaseModel):
    date: datetime
    end_date: datetime
    title: str
    description: str
    priority: PriorityLevel = PriorityLevel.MEDIUM
    assigned_to: int
    created_by: int
    status: Optional[str] = "planned"
    task_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_firebase(cls, data: dict) -> "Task":
        """
        Создаёт объект Task из данных Firebase.
        """
        try:
            return cls(
                date=datetime.fromisoformat(data["date"]),
                end_date=datetime.fromisoformat(data["end_date"]),
                title=data.get("title", ""),
                description=data.get("description", ""),
                priority=PriorityLevel.from_str(data.get("priority", "medium")),
                assigned_to=int(data.get("assigned_to", 0)),
                created_by=int(data.get("created_by", 0)),
                status=data.get("status", "planned"),
                task_id=data.get("task_id"),
            )
        except Exception as e:
            app_logger.error(f"Error creating Task from Firebase data: {e}")
            raise

    @classmethod
    def create(cls, task_data: dict) -> "Task":
        """
        Создаёт задачу в Firebase.
        """
        try:
            task = cls.from_firebase(task_data)
            task_ref = db.reference(f'tasks/{task.date.strftime("%Y-%m-%d")}_{task.assigned_to}')
            task_ref.set(task.dict())
            app_logger.info(f"Task created successfully for {task.assigned_to} on {task.date}.")
            return task
        except ValidationError as e:
            app_logger.error(f"Validation error while creating task: {e}")
            raise
        except Exception as error:
            app_logger.error(f"Error creating task: {error}")
            raise

    @classmethod
    def get_by_assignee(cls, tg_id: Optional[str]) -> List["Task"]:
        if not tg_id:
            raise ValueError("Parameter 'tg_id' must not be None or empty.")

        try:
            tasks_ref = db.reference('tasks')
            tasks_snapshot = tasks_ref.order_by_child('assigned_to').equal_to(tg_id).get()
            return [cls(**task_data) for task_data in tasks_snapshot.values()] if tasks_snapshot else []
        except Exception as error:
            app_logger.error(f"Error retrieving tasks for {tg_id}: {error}")
            raise

    @classmethod
    def get_by_creator(cls, tg_id: Optional[str]) -> List["Task"]:
        if not tg_id:
            raise ValueError("Parameter 'tg_id' must not be None or empty.")

        try:
            tasks_ref = db.reference('tasks')
            tasks_snapshot = tasks_ref.order_by_child('created_by').equal_to(tg_id).get()
            return [cls(**task_data) for task_data in tasks_snapshot.values()] if tasks_snapshot else []
        except Exception as error:
            app_logger.error(f"Error retrieving tasks for {tg_id}: {error}")
            raise

    @classmethod
    def get_by_filter(cls, filters: Optional[dict] = None) -> List["Task"]:
        """
        Получает задачи с использованием заданных фильтров.
        :param filters: Словарь фильтров, где ключ — поле, а значение — значение для фильтрации.
        :return: Список задач, соответствующих фильтрам.
        """
        try:
            tasks_ref = db.reference('tasks')
            if not filters:
                # Если фильтры не заданы, возвращаем все задачи
                tasks_snapshot = tasks_ref.get()
            else:
                # Применяем фильтры
                query = tasks_ref
                for key, value in filters.items():
                    query = query.order_by_child(key).equal_to(value)
                tasks_snapshot = query.get()

            # Проверяем, что snapshot возвращает словарь
            if isinstance(tasks_snapshot, dict):
                return [cls.from_firebase(task_data) for task_data in tasks_snapshot.values()]
            else:
                app_logger.info("No tasks found with the given filters.")
                return []
        except Exception as error:
            app_logger.error(f"Error retrieving tasks with filters {filters}: {error}")
            raise

    @classmethod
    def get_all(cls) -> List["Task"]:
        """
        Получает список всех задач.
        """
        try:
            tasks_ref = db.reference('tasks')
            tasks_snapshot = tasks_ref.get()
            # Проверяем, что snapshot возвращает словарь
            if isinstance(tasks_snapshot, dict):
                return [
                    cls.from_firebase(task_data)
                    for task_data in tasks_snapshot.values()
                ]
            else:
                app_logger.info("No tasks found in the database.")
                return []
        except Exception as error:
            app_logger.error(f"Error retrieving all tasks: {error}")
            raise

    @classmethod
    def update_task_status(cls, task_id: str, new_status: str) -> Optional["Task"]:
        """
        Обновляет статус задачи.
        """
        try:
            task_ref = db.reference(f'tasks/{task_id}')
            task_ref.update({"status": new_status})
            updated_data = task_ref.get()
            return cls.from_firebase(updated_data) if updated_data else None
        except Exception as error:
            app_logger.error(f"Error updating task {task_id}: {error}")
            raise

    @classmethod
    def update_task_assigned(cls, task_id: str) -> Optional["Task"]:
        """
        Сбрасывает назначенного сотрудника.
        """
        try:
            task_ref = db.reference(f'tasks/{task_id}')
            task_ref.update({"assigned_to": 0})
            updated_data = task_ref.get()
            return cls.from_firebase(updated_data) if updated_data else None
        except Exception as error:
            app_logger.error(f"Error updating task {task_id}: {error}")
            raise

    @classmethod
    def delete(cls, task_id: str) -> None:
        """
        Удаляет задачу.
        """
        try:
            task_ref = db.reference(f'tasks/{task_id}')
            task_ref.delete()
            app_logger.info(f"Task {task_id} deleted successfully.")
        except Exception as error:
            app_logger.error(f"Error deleting task {task_id}: {error}")
            raise
