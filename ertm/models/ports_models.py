from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
import enum
from pip._vendor.urllib3.connection import port_by_scheme

class PortTypes(enum.Enum):
    SERIAL = "serial"
    WIRELESS = "wireless"
    ETHERNET = "ethernet"
    FIBER = "fibers"
    GPON = "gpon"
    ADSL = "adsl"
    VDSL = "vdsl"
    XHDSL = "xhdsl"    
    
class PortStatuses(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"
    CRITICAL = "critical"
    WARNING = "warning"
    DOWN = "down"
    DISABLED = "disabled"




class Port(Base):
    __tablename__ = 'ports'
    
    id = Column(Integer, primary_key=True)
    port_name = Column(String, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    port_status = Column(Enum(PortStatuses), nullable=False)
    port_type = Column(Enum(PortTypes), nullable=False)
    port_speed = Column(Integer, nullable=True)
    port_description = Column(String, nullable=True)
    
    # Связь с устройством
    device = relationship("Device", back_populates="ports")
    
    # Связь с абонентами
    subscribers = relationship("Subscriber", back_populates="port")
