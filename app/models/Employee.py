from typing import Optional, List

from pydantic import BaseModel


class Employee(BaseModel):
    id: str
    name: str
    tg_id: Optional[int] = None

    @classmethod
    def from_tuple(cls, data: tuple) -> "Employee":
        return cls(id=data[1], name=data[0])

    @staticmethod
    def get_all_employees() -> List["Employee"]:
        employees = [("Alice", "1"), ("Bob", "2"), ("Charlie", "3")]
        return [Employee.from_tuple(emp) for emp in employees]
