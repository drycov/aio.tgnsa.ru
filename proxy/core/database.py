import aiosqlite
from datetime import datetime
from proxy.config import DB_FILE, logger


async def init_db():
    """
    Инициализация базы данных. Создает таблицу пользователей, если она не существует.
    """
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                token TEXT UNIQUE NOT NULL,
                token_expiry DATETIME NOT NULL
            )
        """)
        await db.commit()
        logger.info("База данных инициализирована.")


async def add_user(username, token, expiry_date):
    """
    Добавление нового пользователя в базу данных.

    :param username: Имя пользователя.
    :param token: Уникальный токен для пользователя.
    :param expiry_date: Срок действия токена.
    :raises ValueError: Если пользователь с таким именем уже существует.
    """
    async with aiosqlite.connect(DB_FILE) as db:
        try:
            await db.execute("""
                INSERT INTO users (username, token, token_expiry) 
                VALUES (?, ?, ?)
            """, (username, token, expiry_date.isoformat()))
            await db.commit()
            logger.info(f"Пользователь '{username}' добавлен.")
        except aiosqlite.IntegrityError as e:
            logger.error(f"Ошибка добавления пользователя '{username}': {e}")
            raise ValueError("Пользователь уже существует.") from e


async def list_users():
    """
    Получение списка всех пользователей из базы данных.

    :return: Список кортежей (username, token, token_expiry).
    """
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT username, token, token_expiry 
            FROM users
        """) as cursor:
            rows = await cursor.fetchall()
            users = []
            for username, token, expiry in rows:
                expiry_date = datetime.fromisoformat(expiry)
                users.append((username, token, expiry_date))
            logger.info(f"Найдено {len(users)} пользователей.")
            return users
