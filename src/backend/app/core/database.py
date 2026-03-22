"""
SQLAlchemy 引擎、Session、Base、get_db。
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import DATABASE_URL, SQL_ECHO

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=SQL_ECHO,
    connect_args={
        "connect_timeout": 10,
        "keepalives_idle": 30,
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import app.models  # noqa: F401 — 註冊所有 ORM 類到 Base.metadata

    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")
