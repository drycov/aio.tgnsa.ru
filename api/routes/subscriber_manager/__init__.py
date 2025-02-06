from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from api.database import SessionLocal, engine
from ertm.models import Device, Port, Subscriber
from ertm.schemas import DeviceSchema, PortSchema, SubscriberSchema

from fastapi import APIRouter, HTTPException

from bot.bot_instance import bot

SubscriberManager = APIRouter()

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@SubscriberManager.get("/devices", response_model=List[DeviceSchema])
def get_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()

@SubscriberManager.get("/ports", response_model=List[PortSchema])
def get_ports(db: Session = Depends(get_db)):
    return db.query(Port).all()

@SubscriberManager.get("/subscribers", response_model=List[SubscriberSchema])
def get_subscribers(db: Session = Depends(get_db)):
    return db.query(Subscriber).all()

@SubscriberManager.post("/devices", response_model=DeviceSchema)
def create_device(device: DeviceSchema, db: Session = Depends(get_db)):
    new_device = Device(**device.dict())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device

@SubscriberManager.post("/ports", response_model=PortSchema)
def create_port(port: PortSchema, db: Session = Depends(get_db)):
    new_port = Port(**port.dict())
    db.add(new_port)
    db.commit()
    db.refresh(new_port)
    return new_port

@SubscriberManager.post("/subscribers", response_model=SubscriberSchema)
def create_subscriber(subscriber: SubscriberSchema, db: Session = Depends(get_db)):
    new_subscriber = Subscriber(**subscriber.dict())
    db.add(new_subscriber)
    db.commit()
    db.refresh(new_subscriber)
    return new_subscriber