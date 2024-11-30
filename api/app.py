import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator

import firebase_admin
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware import Middleware
from fastapi.routing import APIRoute
from firebase_admin import credentials
from jose import jwt, JWTError  # Установите библиотеку `python-jose` для работы с JWT
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from api.routes import register_routes
from bot.bot_module import bot_manager
from bot.utils import JWTManager
from bot.utils.logger_instance import app_logger
from config import Config
from healthy import Healthy
from housekeeper import Housekeeper

EXCLUDE_PATHS = ["/login", "/docs", "/openapi.json", "/api/ping"]  # Пути, которые не требуют авторизации
ALGORITHM = "HS256"


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDE_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        print(auth_header)
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Токен авторизации отсутствует")

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = payload  # Добавляем информацию о пользователе в объект запроса
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f"Ошибка аутентификации: {e}")

        return await call_next(request)


middleware = [
    Middleware(AuthMiddleware)
]


class LoginRequest(BaseModel):
    userid: str
    password: str


class API:
    def __init__(self):
        """
        Инициализация API, Telegram бота и фоновых задач.
        """
        # Инициализация планировщика задач
        self.scheduler = AsyncIOScheduler()

        # Инициализация компонентов приложения
        self.housekeeper = Housekeeper(self.scheduler)
        self.health_manager = Healthy()
        self.users = []  # Локальный список пользователей
        self.bot_task = None  # Хранит задачу для бота

        # Создание FastAPI приложения с жизненным циклом
        self.app = FastAPI(lifespan=self.lifespan, middleware=middleware)

        # Настройка маршрутов
        self.setup_routes()

    def initialize_firebase(self):
        """
        Инициализация Firebase.
        """
        try:
            if not firebase_admin._apps:
                service_account_key = Path(Config.BASE_DIR) / "serviceAccountKey.json"
                app_logger.info(f"Инициализация Firebase с ключом: {service_account_key}")

                if not service_account_key.exists():
                    app_logger.error(f"Файл serviceAccountKey.json не найден: {service_account_key}")
                    sys.exit(1)

                cred = credentials.Certificate(service_account_key)
                firebase_admin.initialize_app(cred, {'databaseURL': Config.FIREBASE_DATABASE_URL})
                app_logger.info("Firebase успешно инициализирован")
        except Exception as e:
            app_logger.error(f"Ошибка при инициализации Firebase: {e}")
            sys.exit(1)

    async def start_bot_task(self):
        """
        Запуск задачи для бота.
        """
        if self.bot_task and not self.bot_task.done():
            app_logger.warning("Бот уже запущен. Повторный запуск отменен.")
            return
        self.bot_task = asyncio.create_task(bot_manager.start_bot())
        app_logger.info("Задача для бота успешно запущена.")

    async def stop_bot_task(self):
        """
        Остановка задачи для бота.
        """
        if self.bot_task and not self.bot_task.done():
            await bot_manager.shutdown_bot()
            self.bot_task.cancel()
            try:
                await self.bot_task
            except asyncio.CancelledError:
                app_logger.info("Задача для бота успешно остановлена.")
        else:
            app_logger.warning("Задача для бота не была запущена или уже завершена.")

    async def restart_bot_task(self):
        """
        Перезапуск задачи для бота.
        """
        await self.stop_bot_task()
        await self.start_bot_task()
        app_logger.info("Задача для бота успешно перезапущена.")

    async def start_resources(self):
        """
        Запуск всех фоновых задач.
        """
        self.housekeeper.schedule_tasks()
        self.scheduler.start()

        asyncio.create_task(self.housekeeper.run())
        # Инициализация и запуск HealthManager
        if hasattr(self, 'health_manager'):
            self.health_manager.start_scheduler()  # Запуск планировщика задач
            app_logger.info("Health Manager запущен.")
        else:
            app_logger.warning("Health Manager не найден. Пропуск инициализации здоровья системы.")

        await self.start_bot_task()
        app_logger.info("Все ресурсы успешно запущены.")

    async def stop_resources(self):
        """
        Остановка всех фоновых задач.
        """
        # Остановка планировщика HealthManager
        if hasattr(self, 'health_manager'):
            self.health_manager.stop_scheduler()
            app_logger.info("Health Manager остановлен.")

        self.scheduler.shutdown(wait=False)
        await self.stop_bot_task()
        app_logger.info("Все ресурсы успешно остановлены.")

    async def lifespan(self, app: FastAPI) -> AsyncGenerator:
        """
        Настройка жизненного цикла приложения.
        """
        # Инициализация Firebase
        self.initialize_firebase()

        # Запуск ресурсов
        await self.start_resources()
        yield  # Указывает, что приложение готово к обработке запросов

        # Завершение ресурсов
        await self.stop_resources()

    def setup_routes(self):
        """
        Настройка маршрутов API.
        """

        @self.app.post("/login")
        async def login(data: LoginRequest):
            # Пример проверки логина и пароля
            if data.userid == "6818244868" and data.password == "password":
                app_logger.info(f"Авторизация пользователя с userid {data.userid}.")

                # Создание токена JWT
                token = JWTManager.generate_jwt(
                    user_id=int(data.userid) if data.userid.isdigit() else data.userid,
                    secret_key=Config.SECRET_KEY,
                    expires_in=Config.Security.Tokens.ACCESS_TOKEN_EXPIRATION,
                )
                return {"access_token": token, "token_type": "Bearer"}

            raise HTTPException(status_code=401, detail="Неверные учетные данные")

        register_routes(self.app)

    def list_routes(self):
        """
        Получает список всех маршрутов в приложении.
        """
        routes = []
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                route_info = {
                    "path": route.path,
                    "name": route.name,
                    "methods": list(route.methods - {"HEAD", "OPTIONS"}),
                }
                routes.append(route_info)
        return routes

    def get_app(self) -> FastAPI:
        """
        Возвращает объект FastAPI для запуска.
        """
        return self.app
