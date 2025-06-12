# app/api/server.py
import os

import uvicorn
from fastapi import FastAPI

from app.core.config import debug_mode, logger, settings

app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


def run_api():
    host = settings.api.API_HOST
    port = settings.api.API_PORT
    workers = 1 if debug_mode else settings.api.API_WORKERS

    logger.info(
        f"🌐 Запуск API-сервера на {host}:{port} "
        f"(режим: {'отладка' if debug_mode else 'продакшн'}, процессов: {workers})..."
    )

    uvicorn.run(
        "app.api.server:app",
        host=host,
        port=port,
        workers=workers,
        reload=debug_mode,
        log_level="debug" if debug_mode else "info",
    )
