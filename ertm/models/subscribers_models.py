from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum,Boolean, Date
from sqlalchemy.orm import relationship
from .base import Base
import enum
from typing import Union


# Типы клиентов
class ClientTypes(enum.Enum):
    INDIVIDUAL = "individual"  # Физическое лицо
    BUSINESS = "business"  # Юридическое лицо
    GOVERNMENT = "government"  # Государственная организация
    NON_PROFIT = "non_profit"  # Некоммерческая организация
    STARTUP = "startup"  # Стартап
    EDUCATIONAL = "educational"  # Образовательное учреждение
    HEALTHCARE = "healthcare"  # Медицинская организация
    FINANCIAL = "financial"  # Финансовая организация (банк, страховая)
    TELECOM = "telecom"  # Телекоммуникационная компания
    INDUSTRIAL = "industrial"  # Промышленное предприятие
    RETAIL = "retail"  # Розничный бизнес
    ENTERTAINMENT = "entertainment"  # Развлекательная индустрия (кино, музыка, спорт)
    TRANSPORT = "transport"  # Логистика и транспортные компании
    ENERGY = "energy"  # Энергетическая компания
    AGRICULTURE = "agriculture"  # Сельское хозяйство
    KTZH = "ktzhm"
class ClientStatuses(enum.Enum):
    ACTIVE = "active"  # Активный
    INACTIVE = "inactive"  # Неактивный
    BLOCKED = "blocked"  # Заблокированный
    DEBTOR = "debtor"  # Дебитор (имеет задолженность)
    SUSPENDED = "suspended"  # Временная приостановка
    TERMINATED = "terminated"  # Окончательно отключён
    PENDING = "pending"  # Ожидает активации
    RESERVED = "reserved"  # Бронирование (зарезервировано)
    DAMAGED = "damaged"  # Повреждён (есть технические неисправности)


class Subscriber(Base):
    __tablename__ = 'subscribers'
    
    id = Column(Integer, primary_key=True)
    subscriber_name = Column(String, nullable=False)
    port_id = Column(Integer, ForeignKey('ports.id'), nullable=False)
    ip_address = Column(String, nullable=True)  # IP адрес
    tv_ott = Column(Boolean, default=False)  # ТВ OTT (True/False)
    client_name_or_device = Column(String, nullable=False)  # Ф.И.О./название оборудования подключенного к порту
    client_address = Column(String, nullable=False)  # Адрес абонента/место установки оборудования
    client_type = Column(Enum(ClientTypes), nullable=False)  # Тип (юр/физ лицо и т. д.)
    tariff_plan = Column(String, nullable=False)  # Тарифный план
    connection_date = Column(Date, nullable=True)  # Дата подключения/переоформления
    disconnection_date = Column(Date, nullable=True)  # Дата снятия
    mac_address = Column(String, nullable=True)  # MAC-адрес
    status = Column(Enum(ClientStatuses), nullable=True)  # Статус (например, "свободен", "занят")
    notes = Column(String, nullable=True)  # Примечания

    # Связь с портом
    port = relationship("Port", back_populates="subscribers")
