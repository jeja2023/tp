from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..models import models, schemas
from ..db import crud, get_db
from ..api import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not Found"}}
)

# 创建任务
@router.post("/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_task(db=db, task=task, user_id=current_user.id)

# 获取用户的所有任务
@router.get("/", response_model=List[schemas.Task])
def get_user_tasks(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_tasks_by_user(db=db, user_id=current_user.id)

# 获取单个任务
@router.get("/{task_id}", response_model=schemas.Task)
def get_task(task_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

# 更新任务
@router.put("/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查任务是否存在
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查是否有权限更新任务
    if task.owner_id != current_user.id:
        # 检查是否有编辑权限
        permission = crud.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
        if not permission or permission.permission_type not in ["edit", "admin"]:
            raise HTTPException(status_code=403, detail="没有权限编辑此任务")
    
    # 更新任务
    return crud.update_task(db=db, task_id=task_id, task_update=task_update)

# 授权任务权限
@router.post("/{task_id}/permissions/", response_model=schemas.TaskPermission)
def create_task_permission(
    task_id: int,
    permission: schemas.TaskPermissionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限：任务创建者或有管理员权限的用户可以分享任务
    if task.owner_id != current_user.id:
        # 检查当前用户是否有管理员权限
        user_permission = crud.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
        if not user_permission or not user_permission.can_manage:
            raise HTTPException(status_code=403, detail="只有任务创建者或管理员可以授权权限")
    
    return crud.create_task_permission(db=db, permission=permission, task_id=task_id, shared_by_id=current_user.id)

# 删除任务权限（取消分享）
@router.delete("/{task_id}/permissions/{username}", response_model=dict)
def delete_task_permission(
    task_id: int,
    username: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取要删除权限的用户
    target_user = crud.get_user_by_username(db=db, username=username)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限分级：
    # 1. 任务创建者可以删除任何人的权限
    # 2. 管理员只能删除自己分享的权限
    # 3. 普通用户无法删除权限
    is_owner = task.owner_id == current_user.id
    
    if is_owner:
        # 任务创建者可以删除任何人的权限
        pass
    else:
        # 非创建者，检查是否有管理员权限
        user_permission = crud.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
        if not user_permission or not user_permission.can_manage:
            raise HTTPException(status_code=403, detail="没有权限管理任务分享")
        
        # 获取要删除的权限记录
        target_permission = crud.get_user_task_permission(db=db, task_id=task_id, user_id=target_user.id)
        if not target_permission:
            raise HTTPException(status_code=404, detail="未找到该用户的权限记录")
        
        # 检查要删除的权限是否是当前用户分享的
        if target_permission.shared_by_id != current_user.id:
            raise HTTPException(status_code=403, detail="非任务创建者不能取消非自己分享的授权记录")
    
    # 删除权限
    result = crud.delete_task_permission(db=db, task_id=task_id, user_id=target_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="未找到该用户的权限记录")
    
    return {"message": "已成功取消分享"}

# 获取任务的所有图片
@router.get("/{task_id}/images", response_model=List[schemas.Image])
def get_task_images(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 系统管理员可以访问任何任务的图片
    if current_user.is_admin:
        return crud.get_images_by_task(db=db, task_id=task_id)
    
    # 检查用户是否有权限访问该任务
    permission = crud.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
    if not (task.owner_id == current_user.id or permission):
        raise HTTPException(status_code=403, detail="没有权限访问此任务的图片")
    
    return crud.get_images_by_task(db=db, task_id=task_id)

# 获取用户对任务的权限信息
@router.get("/{task_id}/user-permission", response_model=dict)
def get_user_task_permission_info(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查任务是否存在
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查用户是否是任务创建者
    is_owner = task.owner_id == current_user.id
    
    # 如果是创建者，拥有全部权限
    if is_owner:
        return {
            "is_owner": True,
            "can_view": True,
            "can_edit": True,
            "can_upload": True,
            "can_manage": True,
            "can_share": True,
            "permission_type": "owner"
        }
    
    # 获取用户权限
    permission = crud.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
    if not permission:
        raise HTTPException(status_code=403, detail="没有权限访问此任务")
    
    # 返回权限信息
    return {
        "is_owner": False,
        "can_view": True,  # 如果有任何权限，就可以查看
        "can_edit": permission.can_edit,
        "can_upload": permission.can_upload,
        "can_manage": permission.can_manage,
        "can_share": permission.can_manage,  # 管理员权限的用户也可以分享任务
        "permission_type": permission.permission_type
    }

# 删除任务
@router.delete("/{task_id}", response_model=dict)
def delete_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查任务是否存在
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 只有任务创建者可以删除任务
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有任务创建者可以删除任务")
    
    # 删除任务及其所有相关数据
    result = crud.delete_task(db=db, task_id=task_id)
    if not result:
        raise HTTPException(status_code=500, detail="删除任务失败")
    
    return {"message": "任务已成功删除"}

# 获取任务的所有权限记录
@router.get("/{task_id}/permissions", response_model=List[dict])
def get_task_permissions(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查任务是否存在
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限：任务创建者或有管理员权限的用户可以查看权限列表
    is_owner = task.owner_id == current_user.id
    if not is_owner:
        user_permission = crud.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
        if not user_permission or not user_permission.can_manage:
            raise HTTPException(status_code=403, detail="只有任务创建者或管理员可以查看权限列表")
    
    # 获取权限记录
    permissions = db.query(models.TaskPermission).filter(models.TaskPermission.task_id == task_id)
    
    # 如果不是任务创建者，则只能查看自己分享的权限记录
    if not is_owner:
        permissions = permissions.filter(models.TaskPermission.shared_by_id == current_user.id)
    
    permissions = permissions.all()
    
    # 构建包含用户名的权限信息列表
    result = []
    for permission in permissions:
        user = db.query(models.User).filter(models.User.id == permission.user_id).first()
        if user:
            # 获取分享者信息
            shared_by_info = None
            if permission.shared_by_id:
                shared_by = db.query(models.User).filter(models.User.id == permission.shared_by_id).first()
                if shared_by:
                    is_creator = (task.owner_id == permission.shared_by_id)
                    shared_by_info = {
                        "username": shared_by.username,
                        "is_creator": is_creator
                    }
            
            result.append({
                "user_id": permission.user_id,
                "username": user.username,
                "permission_type": permission.permission_type,
                "can_edit": permission.can_edit,
                "can_upload": permission.can_upload,
                "can_manage": permission.can_manage,
                "shared_by": shared_by_info
            })
    
    return result 