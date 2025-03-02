# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./storybook.db"
# 使用内存数据库（测试用）: 
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite 需要
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ORM 模型基类
Base = declarative_base()

# 自动创建表结构（仅在应用启动时执行一次）
def create_tables():
    Base.metadata.create_all(bind=engine)

# 获取数据库连接的依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()