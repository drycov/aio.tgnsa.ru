from datetime import datetime
from typing import List, Optional

from pydantic import (BaseModel, EmailStr, Field, computed_field,
                      field_serializer)


class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @property
    def full_name(self) -> str:
        parts = filter(None, (self.first_name, self.last_name))
        return " ".join(parts) or ""

    class Config:
        # orm_mode = True  # если используете pydantic v1
        from_attributes = True  # если pydantic v2


class UserCreate(UserBase):
    tg_id: int = Field(..., ge=1)
    password: str = Field(..., min_length=8)

    class Config:

        exclude = ["created_at", "updated_at"]  # Exclude these from input


class UserRead(UserBase):
    tg_id: int
    is_active: bool = True
    is_banned: bool = False

    class Config:
        # orm_mode = True
        from_attributes = True


class UserResponse(UserRead):
    id: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        parts = filter(None, (self.first_name, self.last_name))
        return " ".join(parts) or ""

    class Config:
        # orm_mode = True
        from_attributes = True
