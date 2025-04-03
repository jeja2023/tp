from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import pytz
from fastapi import HTTPException
from ..models import models, schemas
from ..utils.logger import setup_logger

# 创建日志记录器
logger = setup_logger("crud_task")

def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    """根据ID获取任务"""
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    company: Optional[str] = None,
    user_id: Optional[int] = None
) -> List[models.Task]:
    """获取任务列表，支持过滤"""
    query = db.query(models.Task)
    
    if status:
        query = query.filter(models.Task.status == status)
    if company:
        query = query.filter(models.Task.company == company)
    if user_id:
        query = query.filter(models.Task.user_id == user_id)
    
    return query.offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate) -> models.Task:
    """创建新任务"""
    try:
        # 创建任务记录
        db_task = models.Task(
            title=task.title,
            description=task.description,
            owner_id=task.user_id,  # 使用 owner_id 而不是 user_id
            created_at=models.get_now_shanghai()  # 使用东八区时间
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        logger.info(f"成功创建任务: {db_task.title}")
        return db_task
        
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate) -> models.Task:
    """更新任务信息"""
    try:
        db_task = get_task(db, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 更新任务信息，只更新非 None 的字段
        update_data = task.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:  # 只更新非 None 的值
                setattr(db_task, field, value)
        
        db.commit()
        db.refresh(db_task)
        
        logger.info(f"成功更新任务: {db_task.title}")
        return db_task
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新任务失败: {str(e)}")

def delete_task(db: Session, task_id: int) -> bool:
    """删除任务"""
    try:
        db_task = get_task(db, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 记录任务标题用于日志
        title = db_task.title
        
        # 删除任务
        db.delete(db_task)
        db.commit()
        
        logger.info(f"成功删除任务: {title}")
        return True
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

def get_tasks_by_company(db: Session, company: str) -> List[models.Task]:
    """根据公司获取任务列表"""
    return db.query(models.Task).filter(models.Task.company == company).all()

def get_tasks_by_user(db: Session, user_id: int) -> List[models.Task]:
    """根据用户ID获取任务列表，包括用户创建的和被分享的任务"""
    try:
        # 获取用户创建的任务
        owned_tasks = db.query(models.Task).filter(models.Task.owner_id == user_id).all()
        
        # 获取被分享给用户的任务
        shared_tasks = db.query(models.Task).join(
            models.TaskPermission,
            models.Task.id == models.TaskPermission.task_id
        ).filter(
            models.TaskPermission.user_id == user_id
        ).all()
        
        # 合并任务列表并去重
        all_tasks = list(set(owned_tasks + shared_tasks))
        
        logger.info(f"成功获取用户ID {user_id} 的任务列表，共 {len(all_tasks)} 条（创建: {len(owned_tasks)}, 分享: {len(shared_tasks)}）")
        return all_tasks
    except Exception as e:
        logger.error(f"获取用户任务列表失败: {str(e)}", exc_info=True)
        # 返回空列表而不是抛出异常，避免服务器错误
        return []

def get_tasks_by_status(db: Session, status: str) -> List[models.Task]:
    """根据状态获取任务列表"""
    return db.query(models.Task).filter(models.Task.status == status).all()

def update_task_status(db: Session, task_id: int, status: str) -> models.Task:
    """更新任务状态"""
    try:
        db_task = get_task(db, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        db_task.status = status
        db_task.updated_at = datetime.now(pytz.UTC)
        
        db.commit()
        db.refresh(db_task)
        
        logger.info(f"成功更新任务状态: {db_task.title} -> {status}")
        return db_task
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"更新任务状态失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新任务状态失败: {str(e)}")

def get_images_by_task(db: Session, task_id: int):
    """获取任务的所有图片"""
    try:
        task = get_task(db, task_id)
        if not task:
            logger.error(f"获取图片失败: 任务 {task_id} 不存在")
            raise HTTPException(status_code=404, detail="任务不存在")
        
        images = db.query(models.Image).filter(models.Image.task_id == task_id).all()
        logger.info(f"成功获取任务 {task_id} 的图片列表，共 {len(images)} 张")
        return images
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取任务图片列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取任务图片列表失败: {str(e)}")

def get_user_by_username(db: Session, username: str):
    """根据用户名获取用户"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_task_permission(db: Session, task_id: int, user_id: int):
    """获取用户对任务的权限"""
    return db.query(models.TaskPermission).filter(
        models.TaskPermission.task_id == task_id,
        models.TaskPermission.user_id == user_id
    ).first()

def create_task_permission(db: Session, permission: schemas.TaskPermissionCreate, task_id: int, shared_by_id: int) -> models.TaskPermission:
    """创建或更新任务权限"""
    try:
        # 获取目标用户
        target_user = get_user_by_username(db, permission.username)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 检查是否已经存在权限
        existing_permission = get_user_task_permission(db, task_id, target_user.id)
        
        # 根据权限类型设置权限
        can_edit = permission.permission_type in ["edit", "admin"]
        can_manage = permission.permission_type == "admin"
        
        if existing_permission:
            # 如果已存在权限，更新权限级别
            existing_permission.permission_type = permission.permission_type
            existing_permission.can_edit = can_edit
            existing_permission.can_manage = can_manage
            existing_permission.shared_by_id = shared_by_id  # 更新分享者
            
            db.commit()
            db.refresh(existing_permission)
            
            logger.info(f"成功更新任务权限: 任务ID={task_id}, 用户={permission.username}, 权限类型={permission.permission_type}")
            return existing_permission
        else:
            # 创建新的权限记录
            db_permission = models.TaskPermission(
                task_id=task_id,
                user_id=target_user.id,
                shared_by_id=shared_by_id,
                permission_type=permission.permission_type,
                can_upload=True,  # 默认允许上传
                can_edit=can_edit,
                can_manage=can_manage
            )
            
            db.add(db_permission)
            db.commit()
            db.refresh(db_permission)
            
            logger.info(f"成功创建任务权限: 任务ID={task_id}, 用户={permission.username}, 权限类型={permission.permission_type}")
            return db_permission
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"创建/更新任务权限失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建/更新任务权限失败: {str(e)}")

def delete_task_permission(db: Session, task_id: int, user_id: int) -> bool:
    """删除任务权限"""
    try:
        # 获取权限记录
        permission = get_user_task_permission(db, task_id, user_id)
        if not permission:
            raise HTTPException(status_code=404, detail="未找到该用户的权限记录")
        
        # 记录用户信息用于日志
        user = db.query(models.User).filter(models.User.id == user_id).first()
        username = user.username if user else "未知用户"
        
        # 删除权限记录
        db.delete(permission)
        db.commit()
        
        logger.info(f"成功删除任务权限: 任务ID={task_id}, 用户={username}")
        return True
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除任务权限失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除任务权限失败: {str(e)}") 