"""
数据库连接和ORM配置模块
此模块负责数据库引擎的配置、会话管理以及密码哈希工具
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv  # 用于加载环境变量
from passlib.context import CryptContext  # 密码哈希和验证

# 加载.env文件中的环境变量
load_dotenv()

# ==================== 数据库配置 ====================
# 从环境变量获取数据库连接字符串，如果不存在则使用默认值
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/wardrobe_db"  # 默认连接字符串（开发环境）
)

# 创建SQLAlchemy引擎，配置连接池和其他参数
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,  # 使用连接池管理数据库连接
    pool_size=10,  # 连接池保持的连接数量
    max_overflow=20,  # 允许超过pool_size的最大连接数
    pool_pre_ping=True,  # 每次从连接池获取连接前检查连接是否有效
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",  # 是否输出SQL语句（调试用）
    connect_args={
        "connect_timeout": 10,  # 连接数据库的超时时间（秒）
        "keepalives_idle": 30,  # TCP保持连接的时间（秒）
    }
)

# ==================== 会话配置 ====================
# 创建会话工厂，用于生成数据库会话实例
SessionLocal = sessionmaker(
    autocommit=False,  # 不自动提交事务
    autoflush=False,  # 不自动刷新会话
    bind=engine,  # 绑定到上面创建的引擎
    expire_on_commit=False  # 提交后不使会话中的对象过期，便于后续使用
)

# ==================== 声明基类 ====================
# 创建所有模型类的基类，用于定义数据库表结构
Base = declarative_base()

# ==================== 密码安全工具 ====================
# 创建密码上下文，使用bcrypt算法进行密码哈希和验证
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== 数据库会话依赖注入函数 ====================
def get_db():
    """
    数据库会话生成器函数

    用于FastAPI等框架的依赖注入，每个请求获取一个独立的数据库会话
    请求结束后自动关闭会话，确保连接释放回连接池

    Yields:
        Session: SQLAlchemy数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db  # 将会话提供给请求使用
    finally:
        db.close()  # 请求结束后确保关闭会话


# ==================== 密码工具函数 ====================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配

    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的哈希密码

    Returns:
        bool: 密码匹配返回True，否则返回False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    将明文密码转换为安全的哈希值

    Args:
        password: 需要哈希的明文密码

    Returns:
        str: 哈希后的密码字符串
    """
    return pwd_context.hash(password)


# ==================== 数据库初始化函数 ====================
def init_db():
    """
    初始化数据库，创建所有定义的表

    需要在models模块导入后调用，执行所有继承Base的模型类的建表操作
    """
    from models import Base  # 延迟导入避免循环依赖
    Base.metadata.create_all(bind=engine)  # 创建所有表
    print("数据库表创建完成")