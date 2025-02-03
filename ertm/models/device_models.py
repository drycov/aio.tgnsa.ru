from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Device(Base):
    """
    Модель для хранения информации об устройствах.
    """
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Уникальный идентификатор
    host = Column(String, nullable=False, default='Неизвестный хост')  # Хост устройства
    vendor = Column(String, nullable=False, default='Неизвестный vendor')  # Производитель устройства
    sys_name = Column(String, nullable=False, default='Неизвестное имя')  # Системное имя устройства
    model = Column(String, nullable=False, default='Неизвестная модель')  # Модель устройства
    latitude = Column(Float, nullable=False, default=0.0)  # Широта местоположения
    longitude = Column(Float, nullable=False, default=0.0)  # Долгота местоположения
    address = Column(String, nullable=False, default='Неизвестный адрес')  # Адрес устройства

    # Уникальное ограничение для комбинации полей
    __table_args__ = (
        UniqueConstraint('host', 'sys_name', 'model', name='uq_device_host_sysname_model'),
    )
    
    # Связь с портами
    ports = relationship("Port", back_populates="device")
    
    def __repr__(self):
        """
        Возвращает строковое представление объекта для отладки.
        """
        return (
            f"<Device(id={self.id}, host='{self.host}', vendor='{self.vendor}', "
            f"sys_name='{self.sys_name}', model='{self.model}', "
            f"latitude={self.latitude}, longitude={self.longitude}, "
            f"address='{self.address}')>"
        )


