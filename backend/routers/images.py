from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import models, schemas
from ..db import crud, get_db
from ..api import get_current_user
from datetime import datetime
import shutil
import json
import os
import re

router = APIRouter(
    prefix="/images",
    tags=["images"],
    responses={404: {"description": "Not Found"}}
)

# 上传图片
@router.post("/{task_id}", response_model=schemas.Image)
async def upload_image(
    task_id: int,
    file: UploadFile = File(...),
    time: str = Form(...),
    location: str = Form(...),
    description: Optional[str] = Form(None),
    transportation: str = Form(...),
    gps_latitude: Optional[str] = Form(None),
    gps_longitude: Optional[str] = Form(None),
    people_involved: str = Form("[]"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查任务是否存在
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查用户是否有权限上传图片
    if task.owner_id != current_user.id:
        permission = crud.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
        if not permission or not permission.can_upload:
            raise HTTPException(status_code=403, detail="没有上传权限")
    
    # 创建目录结构：uploads/task_{task_id}/
    task_dir = f"uploads/task_{task_id}"
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)
    
    # 保存文件
    file_extension = os.path.splitext(file.filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{timestamp}_{file.filename}"
    file_path = f"{task_dir}/{file_name}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 修改file_path变量，只保存相对路径，去掉"uploads/"前缀
    relative_path = f"task_{task_id}/{file_name}"
    
    # 解析时间
    try:
        image_time = datetime.fromisoformat(time)
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式不正确")
    
    # 解析坐标
    lat = float(gps_latitude) if gps_latitude else None
    lng = float(gps_longitude) if gps_longitude else None
    
    # 解析人员信息
    try:
        people = json.loads(people_involved)
        people_data = []
        for person in people:
            people_data.append(schemas.PersonInvolvedCreate(
                name=person.get("name", ""),
                id_number=person.get("id_number", ""),
                household_registration=person.get("household_registration", "")
            ))
    except json.JSONDecodeError:
        people_data = []
    
    # 准备图片数据
    image_data = schemas.ImageCreate(
        task_id=task_id,
        file_path=relative_path,
        time=image_time,
        location=location,
        description=description,
        gps_latitude=lat,
        gps_longitude=lng,
        transportation=transportation,
        people_involved=people_data,
        created_by=current_user.username
    )
    
    # 创建图片记录
    image = crud.create_image(db=db, image=image_data, file_path=file_path)
    
    return image

# 获取图片详情
@router.get("/{image_id}", response_model=schemas.Image)
def get_image(
    image_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image = crud.get_image(db=db, image_id=image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    task = crud.get_task(db=db, task_id=image.task_id)
    
    # 检查权限
    # 系统管理员可以查看任何图片
    if current_user.is_admin:
        return image
        
    # 非系统管理员需要检查任务权限
    if task.owner_id != current_user.id:
        permission = crud.get_user_task_permission(db=db, task_id=task.id, user_id=current_user.id)
        if not permission:
            raise HTTPException(status_code=403, detail="没有权限查看此图片")
    
    return image

# 更新图片信息
@router.put("/{image_id}", response_model=schemas.Image)
def update_image(
    image_id: int,
    image_data: schemas.ImageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image = crud.get_image(db=db, image_id=image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    task = crud.get_task(db=db, task_id=image.task_id)
    permission = crud.get_user_task_permission(db=db, task_id=task.id, user_id=current_user.id)
    
    # 权限检查：
    # 1. 任务所有者可以编辑任何图片
    # 2. 任务管理员(permission_type=admin)可以编辑任何图片
    # 3. 系统管理员(is_admin=True)可以编辑任何图片
    # 4. 普通用户只能编辑自己上传的图片
    
    # 系统管理员或任务管理员可以编辑任何图片
    is_system_admin = current_user.is_admin
    is_task_admin = permission and permission.permission_type == "admin"
    
    if is_system_admin or is_task_admin:
        # 保存原始的创建者信息
        print(f"管理员编辑图片，原创建者: {image.created_by}")
        image_data.created_by = image.created_by
        return crud.update_image(db=db, image_id=image_id, image_data=image_data)
    
    # 非管理员需要继续检查权限
    is_task_owner = task.owner_id == current_user.id
    is_image_creator = image.created_by == current_user.username
    
    if not (is_task_owner or (permission and permission.can_edit and is_image_creator)):
        if is_image_creator:
            raise HTTPException(status_code=403, detail="您没有编辑此图片的权限")
        else:
            raise HTTPException(status_code=403, detail="您只能编辑自己上传的图片")
    
    # 保存原始的创建者信息
    print(f"普通权限编辑图片，原创建者: {image.created_by}")
    
    # 强制设置创建者为原始创建者，确保不会被覆盖
    image_data.created_by = image.created_by
    
    return crud.update_image(db=db, image_id=image_id, image_data=image_data)

# 删除图片
@router.delete("/{image_id}", response_model=dict)
def delete_image(
    image_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查图片是否存在
    image = crud.get_image(db=db, image_id=image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 获取关联的任务
    task = crud.get_task(db=db, task_id=image.task_id)
    permission = crud.get_user_task_permission(db=db, task_id=task.id, user_id=current_user.id)
    
    # 权限检查：
    # 1. 任务所有者可以删除任何图片
    # 2. 任务管理员(permission_type=admin)可以删除任何图片
    # 3. 系统管理员(is_admin=True)可以删除任何图片
    # 4. 普通用户只能删除自己上传的图片
    
    # 系统管理员或任务管理员可以删除任何图片
    is_system_admin = current_user.is_admin
    is_task_admin = permission and permission.permission_type == "admin"
    
    if is_system_admin or is_task_admin:
        try:
            # 删除物理文件
            file_path = f"uploads/{image.file_path}"
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 删除数据库记录
            # 1. 先删除关联的人员信息
            db.query(models.PersonInvolved).filter(models.PersonInvolved.image_id == image_id).delete()
            
            # 2. 删除图片记录
            db.query(models.Image).filter(models.Image.id == image_id).delete()
            
            db.commit()
            
            return {"message": "图片已成功删除"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"删除图片时出错: {str(e)}")
    
    # 非管理员需要继续检查权限
    is_task_owner = task.owner_id == current_user.id
    is_image_creator = image.created_by == current_user.username
    
    if not (is_task_owner or (permission and permission.can_edit and is_image_creator)):
        if is_image_creator:
            raise HTTPException(status_code=403, detail="您没有删除此图片的权限")
        else:
            raise HTTPException(status_code=403, detail="您只能删除自己上传的图片")
    
    try:
        # 删除物理文件
        file_path = f"uploads/{image.file_path}"
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 删除数据库记录
        # 1. 先删除关联的人员信息
        db.query(models.PersonInvolved).filter(models.PersonInvolved.image_id == image_id).delete()
        
        # 2. 删除图片记录
        db.query(models.Image).filter(models.Image.id == image_id).delete()
        
        db.commit()
        
        return {"message": "图片已成功删除"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除图片时出错: {str(e)}") 