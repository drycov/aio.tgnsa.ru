# app/api/server.py
import uvicorn
from fastapi import FastAPI
from app.core.config import settings, logger

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

def run_api():
    logger.info("🌐 Запуск API-сервера...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
