from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Уникальный идентификатор
    host = Column(String, nullable=False, default='Неизвестный хост')  # Хост устройства
    sys_name = Column(String, nullable=False, default='Неизвестное имя')  # Имя системы
    model = Column(String, nullable=False, default='Неизвестная модель')  # Модель устройства
    latitude = Column(Float, nullable=False, default=0.0)  # Широта
    longitude = Column(Float, nullable=False, default=0.0)  # Долгота
    address = Column(String, nullable=False, default='Неизвестный адрес')  # Адрес

    # Уникальное ограничение
    __table_args__ = (UniqueConstraint('host', 'sys_name', 'model', name='idx_unique_device'),)
