from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from sqlalchemy.orm import Session
import os
import logging
from .key_manager import KeyManager
from ..models import models
from fastapi import HTTPException
from ..config import settings

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别

# 使用KeyManager获取密钥
key_manager = KeyManager()
SECRET_KEY = settings.SECRET_KEY  # 从settings获取密钥

# 从环境变量获取其他配置
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    try:
        logger.info(f"创建令牌: 用户={data.get('sub')}, 过期时间={expire.isoformat()}")
        logger.debug(f"使用的密钥: {SECRET_KEY[:10]}...")
        logger.debug(f"使用的算法: {ALGORITHM}")
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"创建令牌失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建令牌失败: {str(e)}")

def verify_token(token: str, db: Session) -> Optional[models.User]:
    """验证访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        # 直接从数据库查询用户
        user = db.query(models.User).filter(models.User.username == username).first()
        return user
    except JWTError:
        return None
