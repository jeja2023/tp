import os
import re
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict, Field
from dotenv import load_dotenv
import secrets

# 加载.env文件中的环境变量
load_dotenv()

class Settings(BaseSettings):
    """应用配置类"""
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        validate_default=True
    )
    
    # 应用信息
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "图片管理系统")
    PROJECT_DESCRIPTION: str = os.getenv("PROJECT_DESCRIPTION", "图片管理与轨迹记录系统")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "1.0.0")
    
    # 环境设置
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION: bool = ENVIRONMENT == "production"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 服务器设置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # 数据库连接信息
    MYSQL_USER: str = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "tp_database")
    
    # 数据库URL
    DB_URL: str = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    
    # 安全设置
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(default=["*"], exclude=True)  # 默认允许所有来源，禁用环境变量解析
    
    # 文件存储配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    # 高德地图API配置
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")
    
    # 管理员账户设置
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: Optional[str] = os.getenv("ADMIN_PASSWORD")
    ADMIN_COMPANY: str = os.getenv("ADMIN_COMPANY", "系统管理员")
    ADMIN_PHONE: str = os.getenv("ADMIN_PHONE", "13800138000")
    
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

# 创建全局设置实例
settings = Settings()

# 确保必要的目录存在
settings.create_directories() 