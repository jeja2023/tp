from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from ..models import models, schemas
from ..utils import utils
from ..db import crud, get_db
from ..api import get_current_user
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# OAuth2 认证配置
oauth2_router = APIRouter(
    prefix="",  # 空前缀，允许根路径访问
    tags=["auth"]
)

# 用户注册
@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 验证两次密码是否一致
    if user.password != user.password_confirm:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
        
    # 验证用户名是否已存在
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 如果提供了手机号，验证是否已存在
    if user.phone:
        db_user_phone = db.query(models.User).filter(models.User.phone == user.phone).first()
        if db_user_phone:
            raise HTTPException(status_code=400, detail="手机号已被注册")
    
    return crud.create_user(db=db, user=user)

# 获取当前用户信息
@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# 用户登录
@oauth2_router.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否已通过审核
    if not user.is_approved:
        raise HTTPException(
            status_code=403,
            detail="您的账号正在等待管理员审核，请耐心等待",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="账号已被禁用，请联系管理员",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 验证token
@oauth2_router.get("/auth/verify")
async def verify_token(current_user: models.User = Depends(get_current_user)):
    # 如果能够通过get_current_user验证，则token有效
    return {"valid": True, "username": current_user.username}

# 获取所有待审核用户列表（仅管理员可用）
@router.get("/pending", response_model=List[schemas.User])
async def get_pending_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 检查当前用户是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    # 获取所有待审核用户
    pending_users = db.query(models.User).filter(models.User.is_approved == False).all()
    return pending_users

# 审核用户（仅管理员可用）
@router.put("/{user_id}/approve", response_model=schemas.User)
async def approve_user(
    user_id: int, 
    approve: bool = True,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 检查当前用户是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    # 查找要审核的用户
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户审核状态
    user.is_approved = approve
    db.commit()
    db.refresh(user)
    return user

# 设置管理员权限（仅管理员可用）
@router.put("/{user_id}/admin", response_model=schemas.User)
async def set_admin(
    user_id: int, 
    is_admin: bool = True,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 检查当前用户是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    # 查找要设置的用户
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许取消自己的管理员权限
    if user.id == current_user.id and not is_admin:
        raise HTTPException(status_code=400, detail="不能取消自己的管理员权限")
    
    # 更新用户管理员状态
    user.is_admin = is_admin
    db.commit()
    db.refresh(user)
    return user

# 获取所有用户（仅管理员可用）
@router.get("/", response_model=List[schemas.User])
async def get_all_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 检查当前用户是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    # 获取所有用户
    users = db.query(models.User).all()
    return users

# 激活/禁用用户（仅管理员可用）
@router.put("/{user_id}/active", response_model=schemas.User)
async def set_user_active(
    user_id: int, 
    is_active: bool = True,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 检查当前用户是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    # 查找要设置的用户
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许禁用自己
    if user.id == current_user.id and not is_active:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")
    
    # 更新用户激活状态
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user

# 删除用户（仅管理员可用）
@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 检查当前用户是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    # 查找要删除的用户
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许删除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    
    # 删除用户
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}

# 切换用户状态（启用/禁用）
@router.put("/{user_id}/status", response_model=schemas.User)
async def toggle_user_status(
    user_id: int,
    status: schemas.UserStatusUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查当前用户是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    # 查找要更新的用户
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许禁用自己
    if user.id == current_user.id and not status.is_active:
        raise HTTPException(status_code=400, detail="不能禁用自己的账户")
    
    # 更新用户状态
    user.is_active = status.is_active
    db.commit()
    db.refresh(user)
    return user 