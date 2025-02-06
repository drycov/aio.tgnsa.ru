from pydantic import BaseModel
from typing import Optional

class DeviceSchema(BaseModel):
    id: Optional[int]
    host: str
    vendor: str
    sys_name: str
    model: str
    latitude: float
    longitude: float
    address: str
    
    class Config:
        from_attributes = True
