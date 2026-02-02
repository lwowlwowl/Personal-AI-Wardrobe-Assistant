import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from passlib.context import CryptContext
import os

load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/wardrobe_db"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 密码验证函数
def verify_password(plain_password, hashed_password):
    """验证密码是否正确"""
    return pwd_context.verify(plain_password, hashed_password)

# 密码哈希函数
def get_password_hash(password):
    """生成密码哈希值"""
    return pwd_context.hash(password)

# 初始化数据库（创建表）
def init_db():
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")