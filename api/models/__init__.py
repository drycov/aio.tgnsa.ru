from pydantic import BaseModel
from typing import Any, List, Optional


class LoginRequest(BaseModel):
    userid: str
    password: str

class SuccessResponse(BaseModel):
    status: str = "success"
    data: Optional[Any] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[Any] = None
