from fastapi import FastAPI
from sqlalchemy import create_engine, text

from app.core.config import settings

app = FastAPI(title="RAG Platform API")

engine = create_engine(settings.database_url)


@app.get("/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}