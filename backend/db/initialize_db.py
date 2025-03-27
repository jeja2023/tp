"""
数据库初始化脚本
用于首次部署时创建数据库表结构
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
root_dir = current_dir.parent.parent
sys.path.append(str(root_dir))

from backend.utils.logger import setup_logger
from backend.models.models import Base
from backend.db.database import engine, get_db
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

# 使用新的日志配置
logger = setup_logger("db_init")

def initialize_database():
    """初始化数据库表结构"""
    try:
        # 连接到数据库并创建检查器
        inspector = inspect(engine)
        
        # 检查数据库中是否已存在表
        existing_tables = inspector.get_table_names()
        logger.info(f"检测到已存在的表: {existing_tables}")
        
        # 创建所有在模型中定义但在数据库中不存在的表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表结构创建成功")
        
        # 初始化基础数据
        initialize_base_data()
        
        return True
    except Exception as e:
        logger.error(f"初始化数据库失败: {str(e)}", exc_info=True)
        return False

def initialize_base_data():
    """初始化基础数据，如管理员账号等"""
    try:
        # 获取数据库会话
        db = next(get_db())
        
        # 检查是否需要添加初始管理员账号
        from backend.models.models import User
        from passlib.context import CryptContext
        from config import settings
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # 检查是否已存在管理员账号
        admin_exists = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        
        if not admin_exists:
            # 从配置中获取管理员密码，如果未设置则使用默认密码
            admin_password = settings.ADMIN_PASSWORD or "admin123"
            # 创建管理员账号
            hashed_password = pwd_context.hash(admin_password)
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=hashed_password,
                company=settings.ADMIN_COMPANY,
                phone=settings.ADMIN_PHONE,
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("创建管理员账号成功")
        else:
            logger.info("管理员账号已存在，跳过创建")
            
    except Exception as e:
        logger.error(f"初始化基础数据失败: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()

def validate_env_variables():
    """验证必要的环境变量是否已设置"""
    required_vars = [
        "MYSQL_USER", 
        "MYSQL_PASSWORD", 
        "MYSQL_HOST", 
        "MYSQL_PORT", 
        "MYSQL_DB",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "ADMIN_COMPANY",
        "ADMIN_PHONE"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.error("请设置这些环境变量后再运行初始化脚本")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("开始初始化数据库...")
    
    # 验证环境变量
    if not validate_env_variables():
        sys.exit(1)
    
    # 初始化数据库
    if initialize_database():
        logger.info("数据库初始化完成")
    else:
        logger.error("数据库初始化失败")
        sys.exit(1) 