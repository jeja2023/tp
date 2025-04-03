#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import field_validator

# 配置日志
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 预处理环境变量
if "MAX_CONTENT_LENGTH" in os.environ:
    os.environ["MAX_CONTENT_LENGTH"] = os.environ["MAX_CONTENT_LENGTH"].split("#")[0].strip()

class Settings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"
    }
    
    # 环境设置
    ENVIRONMENT: str = "development"  # development, production
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    MAX_CONTENT_LENGTH: int = 16777216  # 16MB
    APP_DEBUG: bool = True
    
    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DB: str = "tp"
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    LOG_DIR: str = "backend/logging/logs"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,gif"
    
    # 地图配置
    MAP_TILE_PATH: str = "frontend/static/js/MAP_zxy"
    MAP_DEFAULT_ZOOM: int = 12
    MAP_MAX_ZOOM: int = 18
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 日志配置
    LOG_FILE: str = "backend/logging/logs/app.log"
    ERROR_LOG_FILE: str = "backend/logging/logs/error.log"
    LOG_LEVEL: str = "INFO"
    ENABLE_FILE_LOGGING: bool = True
    LOG_RETENTION_DAYS: int = 30
    
    # 其他配置
    API_PREFIX: str = "/api"
    CORS_ORIGINS: str = "*"
    
    # 管理员配置
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_COMPANY: str = "开发测试团队"
    ADMIN_PHONE: str = "13800138000"
    
    @field_validator("ALLOWED_EXTENSIONS")
    def parse_allowed_extensions(cls, v: str) -> List[str]:
        return [x.strip() for x in v.split(",")]
    
    @field_validator("CORS_ORIGINS")
    def parse_cors_origins(cls, v: str) -> List[str]:
        if v == "*":
            return ["*"]
        return [x.strip() for x in v.split(",")]
    
    @field_validator("MAX_CONTENT_LENGTH", "MAX_UPLOAD_SIZE", "PORT", "MYSQL_PORT")
    def validate_integer(cls, v: str | int) -> int:
        if isinstance(v, str):
            # 移除注释
            v = v.split("#")[0].strip()
            return int(v)
        return v
    
    @property
    def DB_URL(self) -> str:
        """获取数据库URL"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
    
    @property
    def IS_PRODUCTION(self) -> bool:
        """是否是生产环境"""
        return self.ENVIRONMENT.lower() == "production"
    
    def create_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.UPLOAD_DIR,
            self.OUTPUT_DIR,
            os.path.join("backend", "logging", "logs"),  # 使用正确的日志目录路径
            os.path.join("backend", "temp")  # 将temp目录移动到backend目录下
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")

# 创建设置实例
settings = Settings()

# 输出一些环境信息
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Database: {settings.MYSQL_DB} on {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")

# 确保必要的目录存在
settings.create_directories() 