import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _build_database_url() -> str:
    user = os.getenv("DB_USER", "monitor")
    password = quote_plus(os.getenv("DB_PASSWORD", "monitorpass"))
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_NAME", "monitor")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


def get_engine():
    return create_engine(
        _build_database_url(),
        pool_pre_ping=True,
        future=True,
    )


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
