# app/models/__init__.py
import logging
from sqlalchemy.orm import relationship

from .role import Role
from .user import User, user_roles
from .duty import DutyEscalation, DutyShift, DutyTeam, DutyUser

from app.core.base import Base, autodiscover_models

logger = logging.getLogger(__name__)

# Автоимпортируем все модели
models = autodiscover_models(["app"])
logger.info("Зарегистрировано моделей: %s", [m.__name__ for m in models])


def setup_relationships():
    User.roles = relationship(Role, back_populates="user", lazy="selectin")


__all__ = [
    "User",
    "Role",
    "user_roles",
    "DutyEscalation",
    "DutyShift",
    "DutyTeam",
    "DutyUser",
    "Base",
]
