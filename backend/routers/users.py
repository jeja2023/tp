from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from ..models import models, schemas
from ..utils import utils
from ..utils.password import verify_password, get_password_hash
from ..db.database import get_db
from ..api import get_current_user
from typing import List
from ..crud import user as crud_user
from ..crud import logs as crud_logs

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
    db_user = crud_user.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 如果提供了手机号，验证是否已存在
    if user.phone:
        db_user_phone = db.query(models.User).filter(models.User.phone == user.phone).first()
        if db_user_phone:
            raise HTTPException(status_code=400, detail="手机号已被注册")
    
    return crud_user.create_user(db=db, user=user)

# 获取当前用户信息
@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# 用户登录
@oauth2_router.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud_user.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        # 记录登录失败
        crud_logs.log_activity(
            db=db,
            level="WARNING",
            source="AUTH",
            message=f"用户 {form_data.username} 登录失败：用户名或密码错误",
            username=form_data.username
        )
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    if not user.is_approved:
        # 记录未审核用户登录尝试
        crud_logs.log_activity(
            db=db,
            level="WARNING",
            source="AUTH",
            message=f"未审核用户 {form_data.username} 尝试登录",
            user_id=user.id,
            username=form_data.username
        )
        raise HTTPException(
            status_code=401,
            detail="您的账号尚未通过审核，请等待管理员审核"
        )
    
    if not user.is_active:
        # 记录禁用用户登录尝试
        crud_logs.log_activity(
            db=db,
            level="WARNING",
            source="AUTH",
            message=f"已禁用用户 {form_data.username} 尝试登录",
            user_id=user.id,
            username=form_data.username
        )
        raise HTTPException(
            status_code=401,
            detail="您的账号已被禁用，请联系管理员"
        )
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # 记录登录成功
    crud_logs.log_activity(
        db=db,
        level="INFO",
        source="AUTH",
        message=f"用户 {form_data.username} 登录成功",
        user_id=user.id,
        username=form_data.username
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

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
    
    # 记录审核操作
    action = "通过" if approve else "拒绝"
    crud_logs.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} {action}了用户 {user.username} 的审核",
        user_id=current_user.id,
        username=current_user.username
    )
    
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
    
    # 记录管理员权限设置
    action = "授予" if is_admin else "撤销"
    crud_user.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} {action}了用户 {user.username} 的管理员权限",
        user_id=current_user.id,
        username=current_user.username
    )
    
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
    
    # 记录用户状态变更
    action = "激活" if is_active else "禁用"
    crud_user.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} {action}了用户 {user.username} 的账号",
        user_id=current_user.id,
        username=current_user.username
    )
    
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
    
    # 记录要删除的用户名
    deleted_username = user.username
    
    # 删除用户
    db.delete(user)
    db.commit()
    
    # 记录删除操作
    crud_logs.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} 删除了用户 {deleted_username}",
        user_id=current_user.id,
        username=current_user.username
    )
    
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

# 更新用户个人信息 - 修改为PUT方法和更简单的路径
@router.put("/profile", response_model=schemas.User)
async def update_user_profile(
    profile: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取当前用户信息
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新个人信息字段（仅更新提供的字段）
    if profile.company is not None:
        user.company = profile.company
    
    if profile.phone is not None:
        # 检查手机号是否已被其他用户使用
        if profile.phone != user.phone:
            existing_user = db.query(models.User).filter(models.User.phone == profile.phone).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="手机号已被其他用户使用")
        user.phone = profile.phone
    
    # 保存更改
    db.commit()
    db.refresh(user)
    return user

# 同时支持旧的路径以兼容性
@router.post("/profile", response_model=schemas.User)
async def update_user_profile_post(
    profile: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 复用PUT方法的实现
    return await update_user_profile(profile, current_user, db)

# 修改用户密码 - 修改为PUT方法和更简单的路径
@router.put("/password", response_model=dict)
async def change_password(
    password_update: schemas.UserPasswordUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取当前用户信息
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证当前密码
    if not verify_password(password_update.current_password, user.password):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    
    # 更新密码
    user.password = get_password_hash(password_update.new_password)
    
    # 保存更改
    db.commit()
    
    return {"message": "密码已成功更新"}

# 同时支持旧的路径以兼容性
@router.post("/password", response_model=dict)
async def change_password_post(
    password_update: schemas.UserPasswordUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 复用PUT方法的实现
    return await change_password(password_update, current_user, db)

# 同时支持change-password路径以兼容性
@router.post("/change-password", response_model=dict)
async def change_password_compat(
    password_update: schemas.UserPasswordUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 复用PUT方法的实现
    return await change_password(password_update, current_user, db)

# 获取用户列表
@router.get("/", response_model=List[schemas.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户列表，只有管理员可以访问"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看用户列表")
    
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users

# 获取指定用户
@router.get("/{user_id}", response_model=schemas.User)
async def read_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定用户信息，只有管理员可以访问"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看用户信息")
    
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return db_user

# 更新用户审核状态
@router.put("/{user_id}/approve")
async def update_user_approval(
    user_id: int,
    approve: bool,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户审核状态，只有管理员可以操作"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以审核用户")
    
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新审核状态
    db_user.is_approved = approve
    db.commit()
    db.refresh(db_user)
    
    # 记录审核操作
    action = "通过" if approve else "拒绝"
    crud_user.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} {action}了用户 {db_user.username} 的审核",
        user_id=current_user.id,
        username=current_user.username
    )
    
    return {"message": f"用户审核状态已更新：{action}"}

# 更新用户管理员权限
@router.put("/{user_id}/admin")
async def update_user_admin(
    user_id: int,
    is_admin: bool,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户管理员权限，只有管理员可以操作"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以设置管理员权限")
    
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新管理员权限
    db_user.is_admin = is_admin
    db.commit()
    db.refresh(db_user)
    
    # 记录管理员权限设置
    action = "授予" if is_admin else "撤销"
    crud_user.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} {action}了用户 {db_user.username} 的管理员权限",
        user_id=current_user.id,
        username=current_user.username
    )
    
    return {"message": f"用户管理员权限已更新：{action}"}

# 更新用户状态
@router.put("/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户状态，只有管理员可以操作"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以更新用户状态")
    
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户状态
    db_user.is_active = is_active
    db.commit()
    db.refresh(db_user)
    
    # 记录用户状态变更
    action = "激活" if is_active else "禁用"
    crud_user.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} {action}了用户 {db_user.username} 的账号",
        user_id=current_user.id,
        username=current_user.username
    )
    
    return {"message": f"用户状态已更新：{action}"} 