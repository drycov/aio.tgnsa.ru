import asyncio
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from bot.utils.snmp_functions import SNMPFunctions
from config import Config
from ertm.models import Base, Device
from bot.utils.helper_functions import HelperFunctions
from bot.utils.logger_instance import app_logger
from ertm.models.ports_models import Port
from ertm.models.subscribers_models import Subscriber
import re
from collections import defaultdict



class ERTM:

    def __init__(self, db_path: Optional[Path]=None):
        """
        Инициализация базы данных и сессии.
        :param db_path: Путь к базе данных (например, Path("data/ertm.db"))
        """
        self.db_url = f"sqlite:///{db_path or Path(Config.DATA_PATH) / 'ertm.db'}"
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)  # Создание таблиц, если их нет
        self.Session = sessionmaker(bind=self.engine)

    @staticmethod
    def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """
        Вычисляет расстояние между двумя координатами (широта, долгота) в метрах.
        :param coord1: Кортеж (широта, долгота) первой точки.
        :param coord2: Кортеж (широта, долгота) второй точки.
        :return: Расстояние в метрах.
        """
        R = 6371e3  # Радиус Земли в метрах
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat, dlon = lat2 - lat1, lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # Расстояние в метрах

    def get_devices_from_db(self) -> List[Dict[str, Optional[str]]]:
        """
        Получает все устройства из базы данных.
        :return: Список устройств в виде словарей.
        """
        try:
            with self.Session() as session:
                devices = session.query(Device).all()
                HelperFunctions.log_action(f"{__name__}.get_devices_from_db")

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
            app_logger.error(f"Ошибка получения устройств: {e}")
            return []

    def add_device(self, host: str, vendor: str, sys_name: str, model: str,
                   latitude: float, longitude: float, address: str) -> bool:
        """
        Добавляет новое устройство в базу данных.
        :param host: Имя хоста устройства.
        :param vendor: Производитель устройства.
        :param sys_name: Системное имя устройства.
        :param model: Модель устройства.
        :param latitude: Широта местоположения устройства.
        :param longitude: Долгота местоположения устройства.
        :param address: Адрес устройства.
        :return: True, если устройство успешно добавлено, иначе False.
        """
        try:
            with self.Session() as session:
                if session.query(Device).filter_by(host=host, sys_name=sys_name, model=model).first():
                    app_logger.info(f"Устройство {host} уже существует в базе данных.")
                    return False

                new_device = Device(
                    host=host, vendor=vendor, sys_name=sys_name, model=model,
                    latitude=latitude, longitude=longitude, address=address
                )
                session.add(new_device)
                session.commit()

                HelperFunctions.log_action(f"{__name__}.add_device", host)
                app_logger.info(f"Устройство {host} успешно добавлено.")
                return True
        except Exception as e:
            app_logger.error(f"Ошибка добавления устройства: {e}")
            return False

    def add_port_to_device(self, device_id: int, port_name: str) -> bool:
        """
        Добавляет порт к устройству.
        :param device_id: ID устройства.
        :param port_name: Имя порта.
        :return: True, если порт успешно добавлен, иначе False.
        """
        try:
            with self.Session() as session:
                device = session.query(Device).filter_by(id=device_id).first()
                if not device:
                    app_logger.error(f"Устройство с ID {device_id} не найдено.")
                    return False

                if session.query(Port).filter_by(port_name=port_name, device_id=device_id).first():
                    app_logger.info(f"Порт {port_name} уже существует на устройстве {device.host}.")
                    return False

                session.add(Port(port_name=port_name, device_id=device_id))
                session.commit()

                HelperFunctions.log_action(f"{__name__}.add_port_to_device", port_name)
                app_logger.info(f"Порт {port_name} успешно добавлен к устройству {device.host}.")
                return True
        except Exception as e:
            app_logger.error(f"Ошибка добавления порта: {e}")
            return False

    def add_subscriber_to_port(self, port_id: int, subscriber_name: str) -> bool:
        """
        Добавляет абонента к порту.
        :param port_id: ID порта.
        :param subscriber_name: Имя абонента.
        :return: True, если абонент успешно добавлен, иначе False.
        """
        try:
            with self.Session() as session:
                port = session.query(Port).filter_by(id=port_id).first()
                if not port:
                    app_logger.error(f"Порт с ID {port_id} не найден.")
                    return False

                if session.query(Subscriber).filter_by(subscriber_name=subscriber_name, port_id=port_id).first():
                    app_logger.info(f"Абонент {subscriber_name} уже существует на порту {port.port_name}.")
                    return False

                session.add(Subscriber(subscriber_name=subscriber_name, port_id=port_id))
                session.commit()

                HelperFunctions.log_action(f"{__name__}.add_subscriber_to_port", subscriber_name)
                app_logger.info(f"Абонент {subscriber_name} успешно добавлен к порту {port.port_name}.")
                return True
        except Exception as e:
            app_logger.error(f"Ошибка добавления абонента: {e}")
            return False

    def get_ports_and_subscribers(self, device_id: int) -> List[Dict[str, List[Dict[str, str]]]]:
        """
        Получает все порты и абонентов для устройства.
        :param device_id: ID устройства.
        :return: Список портов с абонентами.
        """
        try:
            with self.Session() as session:
                device = session.query(Device).filter_by(id=device_id).first()
                if not device:
                    app_logger.error(f"Устройство с ID {device_id} не найдено.")
                    return []

                HelperFunctions.log_action(f"{__name__}.get_ports_and_subscribers")
                return [
                    {
                        "port_name": port.port_name,
                        "subscribers": [{"subscriber_name": s.subscriber_name} for s in port.subscribers]
                    }
                    for port in device.ports
                ]
        except Exception as e:
            app_logger.error(f"Ошибка получения портов и абонентов: {e}")
            return []
            
    @staticmethod
    async def parse_snmp_mac(target, community="public"):
        """Функция для сбора MAC-адресов и их привязки к интерфейсам.
        Возвращает словарь с портами доступа и транками."""
        try:
            # Запускаем параллельные задачи для получения данных через SNMP
            task_mac_table, task_port_table, task_port_mapping, task_if_table = await asyncio.gather(
                SNMPFunctions.get_multi_oid(target, "1.3.6.1.2.1.17.4.3.1.1", community),  # MAC-адреса
                SNMPFunctions.get_multi_oid(target, "1.3.6.1.2.1.17.4.3.1.2", community),  # Порт для каждого MAC
                SNMPFunctions.get_multi_oid(target, "1.3.6.1.2.1.17.1.4.1.2", community),  # Индексы портов
                SNMPFunctions.get_multi_oid(target, "1.3.6.1.2.1.2.2.1.2", community)      # Имена портов
            )

            # Преобразуем результат задач в строковый формат
            mac_table = HelperFunctions.to_string(task_mac_table)
            port_table = HelperFunctions.to_string(task_port_table)
            port_mapping = HelperFunctions.to_string(task_port_mapping)
            if_table = HelperFunctions.to_string(task_if_table)

            # Проверяем, что все данные получены
            if not mac_table or not port_table or not port_mapping or not if_table:
                return None

            # Словарь для хранения MAC-адресов и их портов
            mac_to_port = defaultdict(list)
            # Словарь для хранения индексов портов и их имен
            port_index_to_name = {}

            # Обрабатываем MAC-адреса и порты
            for mac, port in zip(mac_table, port_table):
                mac_address = ":".join(f"{b:02x}" for b in mac.value)  # Преобразуем MAC в строку
                port_index = port.value  # Получаем индекс порта
                mac_to_port[port_index].append(mac_address)  # Добавляем MAC в список порта

            # Обрабатываем имена портов
            for port_index, port_name in zip(port_mapping, if_table):
                port_index_to_name[port_index.value] = port_name.value.decode()  # Сохраняем имя порта

            # Разделяем порты на доступные и транки
            access_ports = {}  # Порты с одним MAC-адресом
            trunk_ports = {}   # Порты с несколькими MAC-адресами

            for port_index, macs in mac_to_port.items():
                if port_index in port_index_to_name:
                    port_name = port_index_to_name[port_index]
                    if len(macs) <= 3:  # На порту доступа может быть до 3 MAC-адресов
                        access_ports[port_name] = macs
                    else:  # Если MAC-адресов больше 3, это транковый порт
                        trunk_ports[port_name] = macs


            # Возвращаем результат
            return {
                "access_ports": access_ports,
                "trunk_ports": trunk_ports
            }

        except Exception as e:
            # Логирование ошибки
            await HelperFunctions.log_action(f"{__name__}.parse_snmp_mac")
            app_logger.error(f"Error in parse_snmp_mac: {str(e)}")
            return None
        
        