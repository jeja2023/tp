from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库配置
# 从环境变量获取数据库连接信息，如果环境变量不存在则使用默认值
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "029209")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "tp")

# 确定环境
ENV = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENV.lower() == "production"

# 构建MySQL连接URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"

# 创建MySQL引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # 关闭SQL语句日志
    echo_pool=False,  # 关闭连接池日志
    pool_pre_ping=True,  # 自动检测连接是否有效
    pool_recycle=3600,  # 连接回收时间（秒）
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大连接数
    pool_timeout=30  # 连接超时时间
)

# 为每个连接设置时区
@event.listens_for(engine, "connect")
def set_timezone(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET time_zone = '+08:00'")
    try:
        if not IS_PRODUCTION:  # 仅在非生产环境尝试设置全局时区
            cursor.execute("SET GLOBAL time_zone = '+08:00'")  # 设置全局时区
    except:
        pass  # 如果没有权限设置全局时区，则忽略错误
    cursor.execute("SET SESSION time_zone = '+08:00'")  # 设置会话时区
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 数据库会话依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 