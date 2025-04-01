#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import secrets
import logging
from typing import Optional, List
import random
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict, Field
from dotenv import load_dotenv
from backend.utils.key_manager import KeyManager

# 加载.env文件中的环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 自定义生成密钥的函数，避免循环导入
def generate_secret_key():
    """生成新的安全密钥"""
    # 使用KeyManager获取密钥
    key_manager = KeyManager()
    return key_manager.get_current_key()

class Settings(BaseSettings):
    """应用配置类"""
    model_config = ConfigDict(
        env_file=".env",  # 指定.env文件路径
        case_sensitive=True,  # 启用大小写敏感
        validate_default=True,  # 验证默认值
        env_file_encoding="utf-8",
        extra="ignore",
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
    MYSQL_USER: str = Field(default="root", env="MYSQL_USER")
    MYSQL_PASSWORD: str = Field(default="", env="MYSQL_PASSWORD")
    MYSQL_HOST: str = Field(default="localhost", env="MYSQL_HOST")
    MYSQL_PORT: int = Field(default=3306, env="MYSQL_PORT")
    MYSQL_DB: str = Field(default="tp", env="MYSQL_DB")
    
    # 数据库URL
    DB_URL: str = Field(default="", env="DB_URL")
    
    # 安全设置
    SECRET_KEY: str = Field(default_factory=generate_secret_key, env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # 文件存储配置
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    OUTPUT_DIR: str = Field(default="outputs", env="OUTPUT_DIR")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR")
    LOG_FILE: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # 离线地图配置
    MAP_TILE_PATH: str = Field(default="frontend/static/js/MAP_zxy", env="MAP_TILE_PATH")
    MAP_DEFAULT_ZOOM: int = Field(default=11, env="MAP_DEFAULT_ZOOM")
    MAP_MAX_ZOOM: int = Field(default=12, env="MAP_MAX_ZOOM")
    
    # 管理员账户设置
    ADMIN_USERNAME: str = Field(default="admin", env="ADMIN_USERNAME")
    ADMIN_PASSWORD: str = Field(default="Admin@123", env="ADMIN_PASSWORD")
    ADMIN_COMPANY: str = Field(default="开发测试团队", env="ADMIN_COMPANY")
    ADMIN_PHONE: str = Field(default="13800138000", env="ADMIN_PHONE")
    
    # 项目配置
    API_PREFIX: str = "/api"
    
    # 验证器
    @field_validator("ENVIRONMENT")
    def validate_environment(cls, v):
        if v not in ["development", "testing", "production"]:
            raise ValueError("ENVIRONMENT must be one of: development, testing, production")
        return v
    
    @field_validator("MYSQL_USER", "MYSQL_PASSWORD")
    @classmethod
    def validate_db_credentials(cls, v, info):
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError(f"{info.field_name} cannot be empty in production environment")
        return v
    
    @field_validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    def create_directories(self):
        """创建必要的目录"""
        for directory in [self.UPLOAD_DIR, self.OUTPUT_DIR, self.LOG_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")

# 创建设置实例
settings = Settings()

# 输出一些环境信息
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Database: {settings.MYSQL_DB} on {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")

# 确保必要的目录存在
settings.create_directories()