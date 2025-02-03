from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Subscriber(Base):
    __tablename__ = 'subscribers'
    
    id = Column(Integer, primary_key=True)
    subscriber_name = Column(String, nullable=False)
    port_id = Column(Integer, ForeignKey('ports.id'), nullable=False)
    
    # Связь с портом
    port = relationship("Port", back_populates="subscribers")