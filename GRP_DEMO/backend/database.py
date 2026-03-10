import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 默认数据库地址（根据你的日志信息设置）
DEFAULT_PG_URL = "postgresql://wardrobe_user:grp2026@localhost:5432/clothing-db"
DATABASE_URL = os.getenv('DATABASE_URL') or DEFAULT_PG_URL

print(f"尝试连接数据库: {DATABASE_URL}")

# 创建引擎逻辑
try:
    # 针对 PostgreSQL 强制指定客户端编码为 utf8，彻底解决 Windows 下的 UnicodeDecodeError
    connect_args = {}
    if DATABASE_URL.startswith("postgresql"):
        connect_args["client_encoding"] = "utf8"

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False,  # 运行稳定后建议设为 False
        connect_args=connect_args
    )

    # 预检连接：尝试获取一个连接，如果失败会直接跳到 except 分支
    with engine.connect() as conn:
        print("✅ PostgreSQL 数据库连接成功")

except Exception as e:
    print("-" * 50)
    print(f"❌ 数据库连接失败!")
    print(f"原因详情: {e}")
    print("提示：请检查 PostgreSQL 服务是否启动 (services.msc)")
    print("-" * 50)

    # 自动降级到 SQLite 确保后端能启动
    print("⚠️ 正在回退到本地 SQLite 数据库 (dev.db)...")
    DATABASE_URL = 'sqlite:///./dev.db'
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# 创建会话和基类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖项：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    try:
        # 这里需要导入 models 确保 Base 知道有哪些表
        import models
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表结构同步完成")
        return True
    except Exception as e:
        print(f"❌ 数据库表初始化失败: {e}")
        return False


# 脚本直接运行时的简单测试
if __name__ == "__main__":
    init_db()