from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime
import pytz
from fastapi import HTTPException
from ..models import models, schemas
from ..utils.logger import setup_logger
from ..utils.password import get_password_hash, verify_password

# 创建日志记录器
logger = setup_logger("crud_user")

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """根据ID获取用户"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """根据用户名获取用户"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    company: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None
) -> List[models.User]:
    """获取用户列表，支持过滤"""
    query = db.query(models.User)
    
    if company:
        query = query.filter(models.User.company == company)
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    if is_admin is not None:
        query = query.filter(models.User.is_admin == is_admin)
    
    return query.offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """创建新用户"""
    try:
        # 检查用户名是否已存在
        if get_user_by_username(db, user.username):
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 创建用户记录
        db_user = models.User(
            username=user.username,
            password=get_password_hash(user.password),  # 使用哈希后的密码
            company=user.company,
            phone=user.phone,
            is_admin=False,  # 新用户默认不是管理员
            is_active=True,
            is_approved=False  # 新用户默认未审核
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"成功创建用户: {db_user.username}")
        return db_user
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

def update_user(db: Session, user_id: int, user: schemas.UserUpdate) -> models.User:
    """更新用户信息"""
    try:
        db_user = get_user(db, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新用户信息
        update_data = user.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"成功更新用户: {db_user.username}")
        return db_user
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")

def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    try:
        db_user = get_user(db, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 记录用户名用于日志
        username = db_user.username
        
        # 删除用户
        db.delete(db_user)
        db.commit()
        
        logger.info(f"成功删除用户: {username}")
        return True
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """验证用户"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):  # 使用密码哈希验证
        return None
    return user

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """根据ID获取用户"""
    return get_user(db, user_id)

def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
    """根据手机号获取用户"""
    return db.query(models.User).filter(models.User.phone == phone).first()

def get_user_by_company(db: Session, company: str) -> List[models.User]:
    """根据公司获取用户列表"""
    return db.query(models.User).filter(models.User.company == company).all()

def get_user_by_username_and_company(db: Session, username: str, company: str) -> Optional[models.User]:
    """根据用户名和公司获取用户"""
    return db.query(models.User).filter(
        models.User.username == username,
        models.User.company == company
    ).first() 