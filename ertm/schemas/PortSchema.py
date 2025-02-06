from pydantic import BaseModel
from typing import Optional
from enum import Enum

# Enum for PortStatuses
class PortStatusesEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"
    CRITICAL = "critical"
    WARNING = "warning"
    DOWN = "down"
    DISABLED = "disabled"

# Enum for PortTypes
class PortTypesEnum(str, Enum):
    SERIAL = "serial"
    WIRELESS = "wireless"
    ETHERNET = "ethernet"
    FIBER = "fibers"
    GPON = "gpon"
    ADSL = "adsl"
    VDSL = "vdsl"
    XHDSL = "xhdsl"

class PortSchema(BaseModel):
    id: Optional[int]
    port_name: str
    device_id: int
    port_status: PortStatusesEnum
    port_type: PortTypesEnum
    port_speed: Optional[int]
    port_description: Optional[str]
    
    class Config:
        from_attributes = True
