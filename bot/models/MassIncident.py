import uuid
from datetime import datetime
from typing import Optional, List, Dict

from firebase_admin import db
from pydantic import BaseModel, Field, ConfigDict

from bot.utils.logger_instance import app_logger


class MassIncident(BaseModel):
    mi_id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="mi_id")
    station: str
    city: str
    addr: str
    comment: str
    ts: datetime
    te: datetime
    from_user: str = Field(alias="from")
    phone: str
    priority: str

    # Метод для сохранения инцидента в базе данных
    def save_to_db(self) -> None:
        """
        Сохраняет инцидент в базу данных.
        """
        try:
            incident_ref = db.reference(f'incidents/{self.mi_id}')
            incident_ref.set(self.model_dump(by_alias=True))
            app_logger.info(f"Incident {self.mi_id} saved successfully.")
        except Exception as error:
            app_logger.error(f"Error saving incident {self.mi_id}: {error}")
            raise

    # Метод класса для создания инцидента
    @classmethod
    def create(cls, data: dict) -> "MassIncident":
        """
        Создает новый инцидент и сохраняет его в базе данных.

        :param data: Данные инцидента.
        :return: Объект инцидента.
        """
        incident = cls(**data)
        incident.save_to_db()
        return incident

    # Метод класса для получения инцидента по ID
    @classmethod
    def get_by_id(cls, mi_id: str) -> Optional["MassIncident"]:
        """
        Получает инцидент по его ID из базы данных.

        :param mi_id: ID инцидента.
        :return: Инцидент или None, если не найден.
        """
        try:
            incident_ref = db.reference(f'incidents/{mi_id}')
            incident_data = incident_ref.get()

            if isinstance(incident_data, dict):
                return cls(**incident_data)
            else:
                app_logger.warning(f"Incident with ID {mi_id} not found or data format is incorrect.")
                return None
        except Exception as error:
            app_logger.error(f"Error fetching incident {mi_id}: {error}")
            raise

    # Метод класса для получения всех инцидентов
    @classmethod
    def get_all(cls) -> List["MassIncident"]:
        """
        Получает список всех инцидентов из базы данных.

        :return: Список инцидентов.
        """
        try:
            incidents_ref = db.reference('incidents')
            incidents_snapshot = incidents_ref.get()

            if isinstance(incidents_snapshot, dict):
                return [cls(**incident_data) for incident_data in incidents_snapshot.values()]
            else:
                app_logger.info("No incidents found or data format is incorrect.")
                return []
        except Exception as error:
            app_logger.error("Error fetching all incidents: %s", error)
            raise

    # Метод для обновления инцидента
    def update(self, updates: dict) -> Optional["MassIncident"]:
        """
        Обновляет данные инцидента в базе данных.

        :param updates: Словарь с обновлениям данных.
        :return: Обновленный инцидент.
        """
        try:
            incident_ref = db.reference(f'incidents/{self.mi_id}')
            incident_ref.update(updates)

            updated_data = incident_ref.get()

            if isinstance(updated_data, dict):
                self.__dict__.update(**updated_data)
                app_logger.info(f"Incident {self.mi_id} updated successfully.")
                return self
            else:
                app_logger.warning(f"Failed to update incident {self.mi_id}. Data format is incorrect or incident not found.")
                return None
        except Exception as error:
            app_logger.error(f"Error updating incident {self.mi_id}: {error}")
            raise

    # Метод класса для удаления инцидента
    @classmethod
    def delete(cls, mi_id: str) -> None:
        """
        Удаляет инцидент по его ID.

        :param mi_id: ID инцидента.
        """
        try:
            incident_ref = db.reference(f'incidents/{mi_id}')
            incident_ref.delete()
            app_logger.info(f"Incident {mi_id} deleted successfully.")
        except Exception as error:
            app_logger.error(f"Error deleting incident {mi_id}: {error}")
            raise

    # Конфигурация модели для генерации примера
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mi_id": "unique-incident-id",
                "station": "Central Station",
                "city": "New York",
                "addr": "123 Main St",
                "comment": "Power outage",
                "ts": "2023-10-31T08:00:00",
                "te": "2023-10-31T12:00:00",
                "from": "Maintenance",
                "phone": "+1234567890",
                "priority": "High"
            }
        }
    )
