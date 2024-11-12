# Приоритет задачи
from datetime import datetime
from enum import Enum
from typing import Optional, List

from firebase_admin import db
from pydantic import BaseModel, ValidationError

from app.utils.logger_instance import app_logger


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Модель задачи
class Task(BaseModel):
    date: datetime
    end_date: datetime  # Дата окончания задачи
    title: str
    description : str
    priority: PriorityLevel = PriorityLevel.MEDIUM
    assigned_to: int  # ID назначенного сотрудника
    created_by: int  # ID автора задачи
    status: Optional[str] = "planned"

    class Config:
        from_attributes = True

    @classmethod
    def create(cls, task_data: dict) -> "Task":
        try:
            task = cls(**task_data)
            task_ref = db.reference(f'tasks/{task_data["date"].strftime("%Y-%m-%d")}_{task.assigned_to}')
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
    def get_by_assignee(cls, tg_id: str) -> List["Task"]:
        try:
            tasks_ref = db.reference('tasks')
            tasks_snapshot = tasks_ref.order_by_child('assigned_to').equal_to(tg_id).get()
            return [cls(**task_data) for task_data in tasks_snapshot.values()] if tasks_snapshot else []
        except Exception as error:
            app_logger.error(f"Error retrieving tasks for {tg_id}: {error}")
            raise

    @classmethod
    def update_task_status(cls, task_id: str, new_status: str) -> Optional["Task"]:
        try:
            task_ref = db.reference(f'tasks/{task_id}')
            task_ref.update({"status": new_status})
            updated_task = task_ref.get()
            app_logger.info(f"Task {task_id} status updated to {new_status}.")
            return cls(**updated_task) if updated_task else None
        except Exception as error:
            app_logger.error(f"Error updating task {task_id}: {error}")
            raise


    @classmethod
    def update_task_assigned(cls, task_id: str, ) -> Optional["Task"]:
        try:
            task_ref = db.reference(f'tasks/{task_id}')
            task_ref.update({"assigned_to": 0})
            updated_task = task_ref.get()
            app_logger.info(f"Task {task_id} status revoked.")
            return cls(**updated_task) if updated_task else None
        except Exception as error:
            app_logger.error(f"Error updating task {task_id}: {error}")
            raise

    @classmethod
    def delete(cls, task_id: str) -> None:
        try:
            task_ref = db.reference(f'tasks/{task_id}')
            task_ref.delete()
            app_logger.info(f"Task {task_id} deleted successfully.")
        except Exception as error:
            app_logger.error(f"Error deleting task {task_id}: {error}")
            raise
