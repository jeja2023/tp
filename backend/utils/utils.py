from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from sqlalchemy.orm import Session
import os
import logging
from ..utils.key_manager import KeyManager

# 配置日志
logger = logging.getLogger(__name__)

# 使用KeyManager获取密钥
key_manager = KeyManager()
SECRET_KEY = key_manager.get_current_key()  # 从密钥管理器获取密钥

# 从环境变量获取其他配置
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    try:
        logger.info(f"创建令牌: 用户={data.get('sub')}, 过期时间={expire.isoformat()}")
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"创建令牌失败: {str(e)}")
        raise e

def verify_token(token: str, credentials_exception, db: Session):
    # 声明使用全局变量SECRET_KEY
    global SECRET_KEY
    
    try:
        # 记录验证开始
        logger.info(f"开始验证令牌: {token[:10]}...")
        
        # 尝试解码令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("令牌中没有用户名(sub字段)")
            raise credentials_exception
            
        # 令牌解码成功
        exp_time = datetime.fromtimestamp(payload.get("exp"))
        logger.info(f"令牌验证成功: 用户={username}, 过期时间={exp_time.isoformat()}")
        
    except jwt.ExpiredSignatureError:
        # 令牌已过期
        logger.warning(f"令牌已过期")
        raise credentials_exception
    except jwt.JWTClaimsError:
        # 令牌声明无效
        logger.warning(f"令牌声明无效")
        raise credentials_exception
    except jwt.JWTError as e:
        # JWT解码错误
        logger.error(f"JWT解码错误: {str(e)}")
        
        # 尝试使用紧急备份密钥解码
        try:
            # 从keybackups目录获取最新的备份密钥
            backup_files = []
            if os.path.exists("keybackups"):
                backup_files = [f for f in os.listdir("keybackups") if f.startswith('.env.')]
            
            if backup_files:
                # 尝试使用最新的备份密钥
                latest = max(backup_files, key=lambda x: os.path.getmtime(os.path.join("keybackups", x)))
                backup_key = None
                
                try:
                    with open(os.path.join("keybackups", latest), 'r') as f:
                        for line in f:
                            if line.startswith('SECRET_KEY='):
                                backup_key = line.strip().split('=')[1]
                                break
                    
                    if backup_key:
                        logger.info(f"尝试使用备份密钥: {latest}")
                        backup_payload = jwt.decode(token, backup_key, algorithms=[ALGORITHM])
                        username = backup_payload.get("sub")
                        
                        if username:
                            logger.warning(f"使用备份密钥成功解码令牌: 用户={username}, 备份文件={latest}")
                            # 更新当前密钥为可用的备份密钥
                            SECRET_KEY = backup_key
                            logger.warning(f"已临时将当前密钥更新为可用的备份密钥")
                except Exception as inner_error:
                    logger.error(f"尝试备份密钥失败: {str(inner_error)}")
        except Exception as outer_error:
            logger.error(f"处理备份密钥出错: {str(outer_error)}")
            
        # 如果所有尝试都失败，抛出原始异常
        raise credentials_exception
    except Exception as e:
        # 其他未预期的错误
        logger.error(f"验证令牌时发生未预期的错误: {str(e)}")
        raise credentials_exception
    
    # 在函数内部导入以避免循环导入
    from backend.db.crud import get_user_by_username
    user = get_user_by_username(db, username=username)
    if user is None:
        logger.warning(f"未找到用户: {username}")
        raise credentials_exception
        
    logger.info(f"用户验证成功: {username}")
    return user
