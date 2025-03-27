import os
import re
import secrets
import logging
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict, Field
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """应用配置类"""
    model_config = ConfigDict(
        env_file=".env",  # 指定.env文件路径
        case_sensitive=True,  # 启用大小写敏感
        validate_default=True  # 验证默认值
    )
    
    # 应用信息
    PROJECT_NAME: str = Field(default="图片管理系统", env="PROJECT_NAME")
    PROJECT_DESCRIPTION: str = Field(default="图片管理与轨迹记录系统", env="PROJECT_DESCRIPTION")
    PROJECT_VERSION: str = Field(default="1.0.0", env="PROJECT_VERSION")
    
    # 环境设置
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    IS_PRODUCTION: bool = ENVIRONMENT == "production"
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # 服务器设置
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # 数据库连接信息
    MYSQL_USER: str = Field(default="", env="MYSQL_USER")
    MYSQL_PASSWORD: str = Field(default="", env="MYSQL_PASSWORD")
    MYSQL_HOST: str = Field(default="localhost", env="MYSQL_HOST")
    MYSQL_PORT: str = Field(default="3306", env="MYSQL_PORT")
    MYSQL_DB: str = Field(default="tp_database", env="MYSQL_DB")
    
    # 数据库URL
    DB_URL: str = Field(default="", env="DB_URL")
    
    # 安全设置
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # 文件存储配置
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    OUTPUT_DIR: str = Field(default="outputs", env="OUTPUT_DIR")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR")
    LOG_FILE: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # 高德地图API配置
    AMAP_API_KEY: str = Field(default="", env="AMAP_API_KEY")
    
    # 管理员账户设置
    ADMIN_USERNAME: str = Field(default="admin", env="ADMIN_USERNAME")
    ADMIN_PASSWORD: Optional[str] = Field(default=None, env="ADMIN_PASSWORD")
    ADMIN_COMPANY: str = Field(default="系统管理员", env="ADMIN_COMPANY")
    ADMIN_PHONE: str = Field(default="13800138000", env="ADMIN_PHONE")
    
    # 验证器
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        if v not in ["development", "production", "testing"]:
            raise ValueError("ENVIRONMENT must be one of: development, production, testing")
        return v
    
    @field_validator("MYSQL_USER", "MYSQL_PASSWORD")
    @classmethod
    def validate_db_credentials(cls, v, info):
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError(f"{info.field_name} cannot be empty in production environment")
        return v
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("ADMIN_PASSWORD")
    @classmethod
    def validate_admin_password(cls, v):
        # 如果是开发环境，允许使用简单密码
        if os.getenv("ENVIRONMENT", "development") == "development":
            return v
            
        # 生产环境进行严格验证
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$", v):
            raise ValueError("Password must contain uppercase, lowercase, number and special character")
        return v
    
    @field_validator("ADMIN_PHONE")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("Invalid phone number format")
        return v
    
    @field_validator("AMAP_API_KEY")
    @classmethod
    def validate_amap_key(cls, v):
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("AMAP_API_KEY cannot be empty in production environment")
        return v

    def create_directories(self):
        """创建必要的目录"""
        for directory in [self.UPLOAD_DIR, self.OUTPUT_DIR, self.LOG_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")

# 创建全局设置实例
settings = Settings()

# 确保必要的目录存在
settings.create_directories()