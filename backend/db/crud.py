from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models.models import User, Task, TaskPermission, Image, PersonInvolved
from ..models.schemas import UserCreate, TaskCreate, TaskUpdate, TaskPermissionCreate, ImageCreate
from typing import List, Optional
from fastapi import HTTPException
import os
import shutil

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    from ..utils.utils import get_password_hash  # 在函数内部导入以避免循环导入
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username, 
        hashed_password=hashed_password,
        company=user.company,
        phone=user.phone,
        is_approved=False,  # 新用户默认未审核
        is_admin=False      # 新用户默认不是管理员
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_tasks_by_user(db: Session, user_id: int):
    # 查询用户自己创建的任务
    own_tasks = db.query(Task).filter(Task.owner_id == user_id).all()
    
    # 查询分享给用户的任务
    shared_task_ids = db.query(TaskPermission.task_id).filter(TaskPermission.user_id == user_id).all()
    shared_task_ids = [task_id[0] for task_id in shared_task_ids]  # 解包结果元组
    
    shared_tasks = []
    if shared_task_ids:
        shared_tasks = db.query(Task).filter(Task.id.in_(shared_task_ids)).all()
    
    # 合并任务列表并按创建时间排序
    all_tasks = own_tasks + shared_tasks
    
    # 按创建时间排序
    all_tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    # 为每个任务加载owner信息
    for task in all_tasks:
        task.owner = db.query(User).filter(User.id == task.owner_id).first()
    
    return all_tasks

def create_task(db: Session, task: TaskCreate, user_id: int):
    db_task = Task(**task.dict(), owner_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task(db: Session, task_id: int):
    return db.query(Task).filter(Task.id == task_id).first()

def update_task(db: Session, task_id: int, task_update: TaskUpdate):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新任务信息
    for key, value in task_update.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    """删除任务及其相关的所有数据"""
    try:
        # 1. 删除任务相关的所有图片文件
        images = db.query(Image).filter(Image.task_id == task_id).all()
        for image in images:
            file_path = f"uploads/{image.file_path}"
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # 2. 删除任务目录
        task_dir = f"uploads/task_{task_id}"
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir)
        
        # 3. 删除数据库中的相关记录
        # 先删除与图片相关的人员信息
        for image in images:
            db.query(PersonInvolved).filter(PersonInvolved.image_id == image.id).delete()
            
        # 删除图片记录
        db.query(Image).filter(Image.task_id == task_id).delete()
        
        # 删除任务权限记录
        db.query(TaskPermission).filter(TaskPermission.task_id == task_id).delete()
        
        # 最后删除任务本身
        db.query(Task).filter(Task.id == task_id).delete()
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"删除任务出错: {str(e)}")
        return False

def create_task_permission(db: Session, permission: TaskPermissionCreate, task_id: int, shared_by_id: int):
    # 通过用户名获取用户ID
    user = get_user_by_username(db, permission.username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限是否已经存在
    existing_permission = get_user_task_permission(db, task_id, user.id)
    if existing_permission:
        # 更新现有权限
        for key, value in permission.dict(exclude={'username'}).items():
            setattr(existing_permission, key, value)
        
        # 设置分享来源
        existing_permission.shared_by_id = shared_by_id
        
        # 根据permission_type设置权限
        if permission.permission_type == "view":
            existing_permission.can_edit = False
            existing_permission.can_upload = False
            existing_permission.can_manage = False
        elif permission.permission_type == "edit":
            existing_permission.can_edit = True
            existing_permission.can_upload = True
            existing_permission.can_manage = False
        elif permission.permission_type == "admin":
            existing_permission.can_edit = True
            existing_permission.can_upload = True
            existing_permission.can_manage = True
        
        db.commit()
        db.refresh(existing_permission)
        return existing_permission
    
    # 创建权限
    permission_dict = permission.dict(exclude={'username'})
    db_permission = TaskPermission(**permission_dict, user_id=user.id, task_id=task_id, shared_by_id=shared_by_id)
    
    # 根据permission_type设置权限
    if permission.permission_type == "view":
        db_permission.can_edit = False
        db_permission.can_upload = False
        db_permission.can_manage = False
    elif permission.permission_type == "edit":
        db_permission.can_edit = True
        db_permission.can_upload = True
        db_permission.can_manage = False
    elif permission.permission_type == "admin":
        db_permission.can_edit = True
        db_permission.can_upload = True
        db_permission.can_manage = True
    
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def get_user_task_permission(db: Session, task_id: int, user_id: int):
    return db.query(TaskPermission).filter(
        TaskPermission.task_id == task_id,
        TaskPermission.user_id == user_id
    ).first()

def delete_task_permission(db: Session, task_id: int, user_id: int):
    """删除用户的任务权限"""
    permission = get_user_task_permission(db, task_id, user_id)
    if not permission:
        return False
    
    db.delete(permission)
    db.commit()
    return True

def create_image(db: Session, image: ImageCreate, file_path: str):
    # 获取当前任务下最大的序号
    max_seq = db.query(Image).filter(
        Image.task_id == image.task_id
    ).order_by(desc(Image.sequence_number)).first()
    
    sequence_number = (max_seq.sequence_number + 1) if max_seq else 1
    
    # 创建图片记录，只存储文件名而不是完整路径
    db_image = Image(
        task_id=image.task_id,
        file_path=image.file_path.replace('\\', '/'),  # 使用传入的相对路径，并统一为正斜杠
        time=image.time,
        location=image.location,
        description=image.description,
        gps_latitude=image.gps_latitude,
        gps_longitude=image.gps_longitude,
        transportation=image.transportation,
        sequence_number=sequence_number,
        created_by=image.created_by  # 保存创建者
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    # 创建涉事人员记录
    if image.people_involved:
        for person in image.people_involved:
            db_person = PersonInvolved(
                **person.dict(),
                image_id=db_image.id
            )
            db.add(db_person)
        
        db.commit()
    
    return db_image

def update_image(db: Session, image_id: int, image_data: ImageCreate):
    db_image = db.query(Image).filter(Image.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 打印传入的数据，用于调试
    print(f"正在更新图片 ID: {image_id}")
    print(f"传入的创建者: {image_data.created_by}")
    
    # 保存原始的created_by字段和created_at字段
    original_created_by = db_image.created_by
    original_created_at = db_image.created_at
    print(f"原始创建者: {original_created_by}")
    
    # 排除created_by字段和task_id字段的更新
    update_data = image_data.dict(exclude={'people_involved', 'task_id', 'created_by'})  # 排除created_by字段
    print(f"更新字段: {update_data}")
    
    # 分别更新每个字段，确保所有字段都被处理
    for key, value in update_data.items():
        print(f"设置字段 {key} = {value}")
        setattr(db_image, key, value)
    
    # 强制恢复原始的created_by和created_at字段
    db_image.created_by = original_created_by
    db_image.created_at = original_created_at
    print(f"恢复后的创建者: {db_image.created_by}")
    
    # 删除原有的涉事人员记录
    db.query(PersonInvolved).filter(PersonInvolved.image_id == image_id).delete()
    
    # 创建新的涉事人员记录
    for person in image_data.people_involved:
        db_person = PersonInvolved(
            **person.dict(),
            image_id=image_id
        )
        db.add(db_person)
    
    db.commit()
    db.refresh(db_image)
    
    # 验证更新后的结果
    print(f"最终的图片创建者: {db_image.created_by}")
    
    return db_image

def get_images_by_task(db: Session, task_id: int):
    return db.query(Image).filter(
        Image.task_id == task_id
    ).order_by(Image.time).all()

def get_image(db: Session, image_id: int):
    return db.query(Image).filter(Image.id == image_id).first() 