from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import date

# Enum for ClientTypes
class ClientTypesEnum(str, Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    STARTUP = "startup"
    EDUCATIONAL = "educational"
    HEALTHCARE = "healthcare"
    FINANCIAL = "financial"
    TELECOM = "telecom"
    INDUSTRIAL = "industrial"
    RETAIL = "retail"
    ENTERTAINMENT = "entertainment"
    TRANSPORT = "transport"
    ENERGY = "energy"
    AGRICULTURE = "agriculture"
    KTZH = "ktzhm"

# Enum for ClientStatuses
class ClientStatusesEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    DEBTOR = "debtor"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    PENDING = "pending"
    RESERVED = "reserved"
    DAMAGED = "damaged"

class SubscriberSchema(BaseModel):
    id: Optional[int]
    subscriber_name: str
    port_id: int
    ip_address: Optional[str]
    tv_ott: bool = False
    client_name_or_device: str
    client_address: str
    client_type: ClientTypesEnum
    tariff_plan: str
    connection_date: Optional[date]
    disconnection_date: Optional[date]
    mac_address: Optional[str]
    status: Optional[ClientStatusesEnum]
    notes: Optional[str]
    
    class Config:
        from_attributes = True
