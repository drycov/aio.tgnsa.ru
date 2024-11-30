import math
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config
from ertm.models import Base, Device


class ERTM:
    def __init__(self, db_path=None):
        """
        Инициализация базы данных и сессии.
        :param db_path : URL базы данных (например, sqlite:///ertm.db)
        """
        # Устанавливаем путь к базе данных
        if db_path is None:
            db_path = Path(Config.DATA_PATH) / "ertm.db"
        self.db_url = f"sqlite:///{db_path}"  # Формируем URL для SQLAlchemy

        # URL базы данных
        self.engine = None  # Эндинг базы данных
        self.Session = None  # Сессия для работы с базой данных
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)  # Создание таблиц, если их нет
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    # Функция для вычисления расстояния в метрах
    @staticmethod
    def calculate_distance(coord1, coord2):
        R = 6371e3  # Радиус Земли в метрах
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c  # Расстояние в метрах

    # Получение всех устройств из базы данных

    def get_devices_from_db(self):
        try:
            devices = self.session.query(Device).all()
            return [
                {
                    "name": device.host,
                    "sys_name": device.sys_name,
                    "model": device.model,
                    "address": device.address,
                    "coords": [device.latitude, device.longitude],
                }
                for device in devices
            ]
        except Exception as e:
            print(f"Ошибка получения устройств: {e}")
            return []

    # Добавление нового устройства в базу данных
    def add_device(self, host,vendor, sys_name, model, latitude, longitude, address):
        try:
            # Проверка существования устройства
            existing_device = (
                self.session.query(Device)
                .filter_by(host=host, sys_name=sys_name, model=model)
                .first()
            )
            if existing_device:
                print("Устройство уже существует в базе данных.")
                return False

            # Создание нового устройства
            new_device = Device(
                host=host,
                vendor=vendor,
                sys_name=sys_name,
                model=model,
                latitude=latitude,
                longitude=longitude,
                address=address,
            )
            self.session.add(new_device)
            self.session.commit()
            print("Устройство успешно добавлено.")
            return True
        except Exception as e:
            print(f"Ошибка добавления устройства: {e}")
            self.session.rollback()
            return False
