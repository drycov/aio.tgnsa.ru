from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base



class Port(Base):
    __tablename__ = 'ports'
    
    id = Column(Integer, primary_key=True)
    port_name = Column(String, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    
    # Связь с устройством
    device = relationship("Device", back_populates="ports")
    
    # Связь с абонентами
    subscribers = relationship("Subscriber", back_populates="port")
