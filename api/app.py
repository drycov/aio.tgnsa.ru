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




class AuthMiddleware(BaseHTTPMiddleware):
    """
    Промежуточное ПО для проверки JWT токенов.
    """
    async def dispatch(self, request: Request, call_next):
        if request.url.path in Config.Security.EXCLUDE_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Токен авторизации отсутствует")

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.Security.ALGORITHM])
            request.state.user = payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Ошибка аутентификации")

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
        Инициализация API и фоновых задач.
        """
        self.scheduler = AsyncIOScheduler()
        self.housekeeper = Housekeeper(self.scheduler)
        self.health_manager = Healthy()
        self.bot_task = None

        self.app = FastAPI(lifespan=self.lifespan, middleware=[Middleware(AuthMiddleware)])
        self.setup_routes()

    def initialize_firebase(self):
        """
        Инициализация Firebase.
        """
        if firebase_admin._apps:
            return

        service_account_key = Path(Config.BASE_DIR) / "serviceAccountKey.json"
        if not service_account_key.exists():
            app_logger.error(f"Файл serviceAccountKey.json не найден: {service_account_key}")
            sys.exit(1)

        cred = credentials.Certificate(service_account_key)
        firebase_admin.initialize_app(cred, {"databaseURL": Config.FIREBASE_DATABASE_URL})
        app_logger.info("Firebase успешно инициализирован")

    async def manage_bot_task(self, action: str):
        """
        Управление задачей бота (start/stop/restart).
        """
        if action == "start" and (not self.bot_task or self.bot_task.done()):
            self.bot_task = asyncio.create_task(bot_manager.start_bot())
            app_logger.info("Бот успешно запущен.")
        elif action == "stop" and self.bot_task and not self.bot_task.done():
            await bot_manager.shutdown_bot()
            self.bot_task.cancel()
            await asyncio.sleep(0)  # Убеждаемся, что задача завершена
            app_logger.info("Бот успешно остановлен.")
        elif action == "restart":
            await self.manage_bot_task("stop")
            await self.manage_bot_task("start")

    async def lifespan(self, app: FastAPI) -> AsyncGenerator:
        """
        Настройка жизненного цикла приложения.
        """
        self.initialize_firebase()
        self.scheduler.start()
        await self.manage_bot_task("start")
        yield
        self.scheduler.shutdown(wait=False)
        await self.manage_bot_task("stop")

    def setup_routes(self):
        """
        Настройка маршрутов API.
        """

        @self.app.post("/login")
        async def login(data: LoginRequest):
            if data.userid == "6818244868" and data.password == "password":
                token = JWTManager.generate_jwt(
                    user_id=int(data.userid) if data.userid.isdigit() else data.userid,
                    secret_key=Config.SECRET_KEY,
                    expires_in=Config.Security.Tokens.ACCESS_TOKEN_EXPIRATION,
                )
                return {"access_token": token, "token_type": "Bearer"}

            raise HTTPException(status_code=401, detail="Неверные учетные данные")

        register_routes(self.app)

    def get_app(self) -> FastAPI:
        """
        Возвращает объект FastAPI для запуска.
        """
        return self.app