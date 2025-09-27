# app/models/__init__.py
from sqlalchemy.orm import relationship

from .role import Role
from .user import User, user_roles
from .duty import DutyEscalation, DutyShift, DutyTeam, DutyUser
# Отложенная настройка отношений


def setup_relationships():
    User.roles = relationship(Role, back_populates="user", lazy="selectin")


__all__ = ["User", "Role", "user_roles","DutyEscalation", "DutyShift", "DutyTeam", "DutyUser"]
