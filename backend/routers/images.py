from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import models, schemas
from ..db import get_db
from ..api import get_current_user
from ..crud import task as crud_task, image as crud_image
from ..utils.logger import setup_logger
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
    task = crud_task.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查用户是否有权限上传图片
    # 1. 系统管理员可以上传任何任务的图片
    # 2. 任务创建者可以上传图片
    # 3. 有上传权限的用户可以上传图片
    if not current_user.is_admin and task.owner_id != current_user.id:
        permission = crud_task.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
        if not permission or not permission.can_upload:
            raise HTTPException(status_code=403, detail="没有上传权限")
    
    # 创建目录结构：uploads/task_{task_id}/
    task_dir = f"uploads/task_{task_id}"
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)
    
    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{timestamp}{file_extension}"
    file_path = os.path.join(task_dir, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    # 解析人员信息
    try:
        logger = setup_logger("images_router")
        logger.info(f"接收到人员信息JSON字符串: {people_involved}")
        
        raw_people = json.loads(people_involved)
        logger.info(f"解析后的人员数据类型: {type(raw_people)}, 长度: {len(raw_people)}")
        
        if len(raw_people) > 0:
            logger.info(f"第一条人员原始数据: {raw_people[0]}")
        
        people_list = []
        for i, person in enumerate(raw_people):
            # 确保每个人员数据包含所需的字段
            logger.info(f"处理第 {i+1} 个人员数据: {person}")
            
            if isinstance(person, dict) and all(k in person for k in ['name', 'id_number', 'household_registration']):
                # 创建符合PersonInvolvedCreate模型的对象
                people_obj = schemas.PersonInvolvedCreate(
                    name=person['name'],
                    id_number=person['id_number'],
                    household_registration=person['household_registration']
                )
                people_list.append(people_obj)
                logger.info(f"已添加第 {i+1} 个人员: {person['name']}")
            else:
                logger.warning(f"人员数据格式不正确: {person}")
                # 使用默认值创建
                if isinstance(person, dict):
                    people_obj = schemas.PersonInvolvedCreate(
                        name=person.get('name', ''),
                        id_number=person.get('id_number', ''),
                        household_registration=person.get('household_registration', '')
                    )
                    people_list.append(people_obj)
                    logger.info(f"使用默认值添加第 {i+1} 个人员")
        
        logger.info(f"最终处理的人员数据数量: {len(people_list)}")
    except json.JSONDecodeError as e:
        logger.error(f"解析人员JSON数据失败: {str(e)}")
        people_list = []
    except Exception as e:
        logger.error(f"处理人员数据时出错: {str(e)}", exc_info=True)
        people_list = []
    
    # 创建图片记录
    image_data = {
        "task_id": task_id,
        "file_path": file_path,
        "time": datetime.fromisoformat(time),
        "location": location,
        "description": description,
        "transportation": transportation,
        "gps_latitude": float(gps_latitude) if gps_latitude else None,
        "gps_longitude": float(gps_longitude) if gps_longitude else None,
        "created_by": current_user.username,
        "people_involved": people_list
    }
    
    return crud_image.create_image(db=db, image=schemas.ImageCreate(**image_data))

# 获取任务的所有图片
@router.get("/task/{task_id}", response_model=List[schemas.Image])
def get_task_images(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查任务是否存在
    task = crud_task.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查用户是否有权限访问图片
    if task.owner_id != current_user.id:
        permission = crud_task.get_user_task_permission(db=db, task_id=task_id, user_id=current_user.id)
        if not permission or not permission.can_view:
            raise HTTPException(status_code=403, detail="没有查看权限")
    
    return crud_image.get_images_by_task(db=db, task_id=task_id)

# 获取单个图片
@router.get("/{image_id}", response_model=schemas.Image)
def get_image(
    image_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger = setup_logger("images_router")
    logger.info(f"开始处理获取图片请求，图片ID: {image_id}, 用户ID: {current_user.id}")
    
    try:
        # 获取图片信息
        image = crud_image.get_image(db=db, image_id=image_id)
        if not image:
            logger.warning(f"图片不存在，ID: {image_id}")
            raise HTTPException(status_code=404, detail="图片不存在")
        
        logger.info(f"找到图片，任务ID: {image.task_id}")
        # 检查任务是否存在
        task = crud_task.get_task(db=db, task_id=image.task_id)
        if not task:
            logger.warning(f"图片关联的任务不存在，任务ID: {image.task_id}")
            raise HTTPException(status_code=404, detail="任务不存在")
        
        logger.info(f"检查用户权限，用户ID: {current_user.id}, 任务所有者ID: {task.owner_id}")
        # 检查用户是否有权限访问图片
        # 1. 系统管理员可以查看任何图片
        # 2. 任务创建者可以查看图片
        # 3. 有查看权限的用户可以查看图片
        if not current_user.is_admin and task.owner_id != current_user.id:
            permission = crud_task.get_user_task_permission(db=db, task_id=image.task_id, user_id=current_user.id)
            if not permission or permission.permission_type not in ['view', 'edit', 'admin']:
                logger.warning(f"用户没有查看权限，用户ID: {current_user.id}, 任务ID: {image.task_id}")
                raise HTTPException(status_code=403, detail="没有查看权限")
        
        logger.info(f"成功返回图片信息，图片ID: {image_id}")
        return image
    except HTTPException as e:
        logger.error(f"HTTP异常: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"获取图片时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")

# 更新图片信息
@router.put("/{image_id}", response_model=schemas.Image)
def update_image(
    image_id: int,
    image_update: schemas.ImageUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取图片信息
    image = crud_image.get_image(db=db, image_id=image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 检查任务是否存在
    task = crud_task.get_task(db=db, task_id=image.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查用户是否有权限编辑图片
    # 1. 系统管理员可以编辑任何图片
    # 2. 任务创建者可以编辑图片
    # 3. 有编辑权限的用户可以编辑图片
    if not current_user.is_admin and task.owner_id != current_user.id:
        permission = crud_task.get_user_task_permission(db=db, task_id=image.task_id, user_id=current_user.id)
        if not permission or not permission.can_edit:
            raise HTTPException(status_code=403, detail="没有编辑权限")
    
    # 记录接收到的数据用于调试
    logger = setup_logger("images_router")
    logger.info(f"接收到更新请求，图片ID: {image_id}")
    
    # 记录更新数据的键和类型
    update_data_info = {k: type(v).__name__ for k, v in image_update.dict().items() if v is not None}
    logger.info(f"更新数据键和类型: {update_data_info}")
    
    # 特别记录people_involved字段的详细信息
    if image_update.people_involved is not None:
        logger.info(f"人员信息类型: {type(image_update.people_involved).__name__}")
        logger.info(f"人员信息长度: {len(image_update.people_involved)}")
        
        if len(image_update.people_involved) > 0:
            first_person = image_update.people_involved[0]
            logger.info(f"第一个人员信息类型: {type(first_person).__name__}")
            
            if hasattr(first_person, '__dict__'):
                logger.info(f"第一个人员信息属性: {first_person.__dict__}")
            elif isinstance(first_person, dict):
                logger.info(f"第一个人员信息属性: {first_person}")
    
    # 如果提供了人员数据但格式不正确，需要格式化为PersonInvolvedCreate对象
    if image_update.people_involved is not None:
        logger.info(f"开始处理人员信息，原始数据: {image_update.people_involved}")
        
        # 确保人员数据是PersonInvolvedCreate对象列表
        people_list = []
        try:
            for idx, person in enumerate(image_update.people_involved):
                logger.info(f"处理第 {idx+1} 个人员，类型: {type(person).__name__}")
                
                if isinstance(person, dict):
                    # 如果是字典，转换为模型对象
                    logger.info(f"处理人员字典数据: {person}")
                    # 检查所需字段是否存在
                    if not all(k in person for k in ['name', 'id_number', 'household_registration']):
                        logger.warning(f"人员数据缺少必要字段: {person}")
                        # 使用默认值补全缺失字段
                        person_data = {
                            'name': person.get('name', ''),
                            'id_number': person.get('id_number', ''),
                            'household_registration': person.get('household_registration', '')
                        }
                        logger.info(f"补全后的人员数据: {person_data}")
                        people_list.append(schemas.PersonInvolvedCreate(**person_data))
                    else:
                        people_list.append(schemas.PersonInvolvedCreate(**person))
                else:
                    # 已经是模型对象
                    logger.info(f"处理人员模型对象")
                    people_list.append(person)
            
            # 更新为格式化后的列表
            image_update.people_involved = people_list
            logger.info(f"处理后的人员列表长度: {len(people_list)}")
            for idx, p in enumerate(people_list):
                logger.info(f"第 {idx+1} 个处理后的人员: {p}")
        except Exception as e:
            logger.error(f"处理人员信息时出错: {str(e)}", exc_info=True)
            image_update.people_involved = []
    
    try:
        updated_image = crud_image.update_image(db=db, image_id=image_id, image_update=image_update)
        logger.info(f"成功更新图片 {image_id}")
        return updated_image
    except Exception as e:
        logger.error(f"更新图片失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新图片失败: {str(e)}")

# 删除图片
@router.delete("/{image_id}")
def delete_image(
    image_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger = setup_logger("images_router")
    logger.info(f"开始处理删除图片请求，图片ID: {image_id}, 用户ID: {current_user.id}")
    
    try:
        # 获取图片信息
        image = crud_image.get_image(db=db, image_id=image_id)
        if not image:
            logger.warning(f"图片不存在，ID: {image_id}")
            raise HTTPException(status_code=404, detail="图片不存在")
        
        logger.info(f"找到图片记录，任务ID: {image.task_id}")
        
        # 检查任务是否存在
        task = crud_task.get_task(db=db, task_id=image.task_id)
        if not task:
            logger.warning(f"图片关联的任务不存在，任务ID: {image.task_id}")
            raise HTTPException(status_code=404, detail="任务不存在")
        
        logger.info(f"检查用户权限，用户ID: {current_user.id}, 任务所有者ID: {task.owner_id}")
        
        # 检查用户是否有权限删除图片
        # 1. 如果是任务所有者，允许删除
        # 2. 如果是系统管理员，允许删除
        # 3. 如果是任务管理员，允许删除
        # 4. 如果是图片上传者且有编辑权限，允许删除
        if task.owner_id != current_user.id and not current_user.is_admin:
            permission = crud_task.get_user_task_permission(db=db, task_id=image.task_id, user_id=current_user.id)
            
            # 构建详细的错误信息
            error_details = []
            
            if not permission:
                error_details.append("您没有该任务的任何权限")
            else:
                if permission.can_manage:
                    # 任务管理员可以删除任何图片
                    pass
                elif not permission.can_edit:
                    error_details.append("您没有该任务的编辑权限")
                elif image.created_by != current_user.username:
                    error_details.append("您不是该图片的上传者")
            
            if error_details:
                error_message = "无法删除图片，原因：" + "；".join(error_details)
                logger.warning(f"用户没有删除权限，用户ID: {current_user.id}, 任务ID: {image.task_id}, 原因: {error_message}")
                raise HTTPException(status_code=403, detail=error_message)
        
        logger.info("权限验证通过，开始删除图片")
        
        try:
            # 先删除数据库记录（包括关联的涉事人员信息）
            result = crud_image.delete_image(db=db, image_id=image_id)
            if not result:
                logger.error("删除数据库记录失败")
                raise HTTPException(status_code=500, detail="删除数据库记录失败")
            
            logger.info("数据库记录删除成功")
            
            # 如果数据库记录删除成功，再删除物理文件
            if os.path.exists(image.file_path):
                try:
                    os.remove(image.file_path)
                    logger.info(f"物理文件删除成功: {image.file_path}")
                except Exception as e:
                    # 记录错误但不抛出异常，因为数据库记录已经删除
                    logger.error(f"删除物理文件失败: {str(e)}")
            else:
                logger.warning(f"物理文件不存在: {image.file_path}")
            
            logger.info("图片删除操作完成")
            return {"status": "success", "message": "图片删除成功"}
            
        except HTTPException as e:
            logger.error(f"HTTP异常: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"删除图片时发生错误: {str(e)}", exc_info=True)
            db.rollback()
            raise HTTPException(status_code=500, detail=f"删除图片失败: {str(e)}")
            
    except HTTPException as e:
        logger.error(f"HTTP异常: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"处理删除请求时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理删除请求失败: {str(e)}") 