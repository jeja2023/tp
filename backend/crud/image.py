from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import pytz
from fastapi import HTTPException
from ..models import models, schemas
from ..utils.logger import setup_logger
import os
from pathlib import Path

# 创建日志记录器
logger = setup_logger("crud_image")

def get_image(db: Session, image_id: int) -> Optional[models.Image]:
    """根据ID获取图片"""
    try:
        logger.info(f"开始获取图片，ID: {image_id}")
        
        # 检查数据库连接
        if not db:
            logger.error("数据库会话无效")
            raise HTTPException(status_code=500, detail="数据库连接错误")
            
        # 获取图片信息
        try:
            image = db.query(models.Image).filter(models.Image.id == image_id).first()
            logger.info(f"数据库查询完成，结果: {'找到图片' if image else '未找到图片'}")
        except Exception as e:
            logger.error(f"数据库查询失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
            
        if not image:
            logger.warning(f"图片不存在，ID: {image_id}")
            raise HTTPException(status_code=404, detail="图片不存在")
            
        logger.info(f"找到图片，任务ID: {image.task_id}, 文件路径: {image.file_path}")
        
        # 获取任务信息
        try:
            task = db.query(models.Task).filter(models.Task.id == image.task_id).first()
            logger.info(f"任务查询完成，结果: {'找到任务' if task else '未找到任务'}")
        except Exception as e:
            logger.error(f"任务查询失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"任务查询失败: {str(e)}")
            
        if not task:
            logger.warning(f"图片关联的任务不存在，任务ID: {image.task_id}")
            raise HTTPException(status_code=404, detail="图片关联的任务不存在")
            
        # 检查文件是否存在
        if not os.path.exists(image.file_path):
            logger.warning(f"图片文件不存在，路径: {image.file_path}")
            raise HTTPException(status_code=404, detail="图片文件不存在")
            
        # 获取涉事人员信息
        try:
            people = db.query(models.PersonInvolved).filter(
                models.PersonInvolved.image_id == image_id
            ).all()
            logger.info(f"获取到 {len(people)} 个涉事人员信息")
        except Exception as e:
            logger.error(f"获取涉事人员信息失败: {str(e)}", exc_info=True)
            # 不抛出异常，继续返回图片信息
            
        logger.info(f"成功获取图片和任务信息，图片ID: {image_id}, 任务ID: {image.task_id}")
        return image
        
    except HTTPException as e:
        logger.error(f"HTTP异常: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"获取图片失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")

def get_images(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    company: Optional[str] = None,
    user_id: Optional[int] = None,
    task_id: Optional[int] = None
) -> List[models.Image]:
    """获取图片列表，支持过滤"""
    query = db.query(models.Image)
    
    if company:
        query = query.filter(models.Image.company == company)
    if user_id:
        query = query.filter(models.Image.user_id == user_id)
    if task_id:
        query = query.filter(models.Image.task_id == task_id)
    
    return query.order_by(models.Image.created_at.desc()).offset(skip).limit(limit).all()

def create_image(db: Session, image: schemas.ImageCreate) -> models.Image:
    """创建新图片记录"""
    try:
        # 记录人员信息
        if image.people_involved:
            people_count = len(image.people_involved)
            logger.info(f"图片包含 {people_count} 人员信息")
            for i, person in enumerate(image.people_involved):
                logger.info(f"人员 {i+1}: 姓名={person.name}, 证件号={person.id_number}, 户籍={person.household_registration}")
        else:
            logger.info("图片未包含人员信息")
            
        # 创建图片记录
        db_image = models.Image(
            file_path=image.file_path,
            time=image.time,
            location=image.location,
            description=image.description,
            gps_latitude=image.gps_latitude,
            gps_longitude=image.gps_longitude,
            transportation=image.transportation,
            created_by=image.created_by,
            task_id=image.task_id,
            user_id=db.query(models.Task).filter(models.Task.id == image.task_id).first().owner_id,
            created_at=models.get_now_shanghai(),
            updated_at=models.get_now_shanghai()
        )
        
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        logger.info(f"图片记录已创建: ID={db_image.id}")
        
        # 处理关联的人员信息
        if image.people_involved and len(image.people_involved) > 0:
            logger.info(f"开始写入 {len(image.people_involved)} 条人员信息")
            
            try:
                for i, person_data in enumerate(image.people_involved):
                    logger.info(f"处理第 {i+1} 人员信息: {person_data}")
                    
                    # 创建人员记录
                    person = models.PersonInvolved(
                        image_id=db_image.id,
                        name=person_data.name,
                        id_number=person_data.id_number,
                        household_registration=person_data.household_registration
                    )
                    db.add(person)
                    logger.info(f"已添加人员 {i+1} 到数据库会话")
                
                # 提交所有人员信息
                db.commit()
                logger.info(f"所有人员信息已提交到数据库")
            except Exception as e:
                logger.error(f"保存人员信息时出错: {str(e)}", exc_info=True)
                # 注意：即使人员信息保存失败，仍然返回创建的图片记录
                # 这里不回滚，避免图片本身也被删除
        else:
            logger.info("没有人员信息需要保存")
        
        logger.info(f"成功创建图片记录: {db_image.file_path}")
        return db_image
        
    except Exception as e:
        logger.error(f"创建图片记录失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建图片记录失败: {str(e)}")

def delete_image(db: Session, image_id: int) -> bool:
    """删除图片及其文件"""
    try:
        logger.info(f"开始删除图片，ID: {image_id}")
        
        # 获取图片信息
        db_image = get_image(db, image_id)
        if not db_image:
            logger.error(f"图片不存在，ID: {image_id}")
            raise HTTPException(status_code=404, detail="图片不存在")
        
        # 记录文件名用于日志
        filename = db_image.file_path
        logger.info(f"找到图片记录，文件路径: {filename}")
        
        # 开始事务
        try:
            # 删除关联的涉事人员信息
            people = db.query(models.PersonInvolved).filter(
                models.PersonInvolved.image_id == image_id
            ).all()
            logger.info(f"找到 {len(people)} 个关联的涉事人员信息")
            
            for person in people:
                try:
                    db.delete(person)
                    logger.info(f"已删除涉事人员记录，ID: {person.id}")
                except Exception as e:
                    logger.error(f"删除涉事人员记录失败，ID: {person.id}, 错误: {str(e)}")
                    raise
            
            # 删除图片记录
            try:
                db.delete(db_image)
                logger.info("已删除图片记录")
            except Exception as e:
                logger.error(f"删除图片记录失败: {str(e)}")
                raise
            
            # 提交事务
            db.commit()
            logger.info(f"事务提交成功，已删除数据库记录: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"删除数据库记录失败: {str(e)}", exc_info=True)
            db.rollback()
            raise HTTPException(status_code=500, detail=f"删除数据库记录失败: {str(e)}")
            
    except HTTPException as e:
        logger.error(f"HTTP异常: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"删除图片失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除图片失败: {str(e)}")

def get_images_by_company(db: Session, company: str) -> List[models.Image]:
    """根据公司获取图片列表"""
    return db.query(models.Image).filter(models.Image.company == company).all()

def get_images_by_user(db: Session, user_id: int) -> List[models.Image]:
    """根据用户ID获取图片列表"""
    return db.query(models.Image).filter(models.Image.user_id == user_id).all()

def get_images_by_task(db: Session, task_id: int) -> List[models.Image]:
    """根据任务ID获取图片列表"""
    return db.query(models.Image).filter(models.Image.task_id == task_id).all()

def get_images_by_user_and_company(
    db: Session,
    user_id: int,
    company: str
) -> List[models.Image]:
    """根据用户ID和公司获取图片列表"""
    return db.query(models.Image).filter(
        models.Image.user_id == user_id,
        models.Image.company == company
    ).all()

def get_images_by_task_and_company(
    db: Session,
    task_id: int,
    company: str
) -> List[models.Image]:
    """根据任务ID和公司获取图片列表"""
    return db.query(models.Image).filter(
        models.Image.task_id == task_id,
        models.Image.company == company
    ).all()

def get_images_by_user_and_task(
    db: Session,
    user_id: int,
    task_id: int
) -> List[models.Image]:
    """根据用户ID和任务ID获取图片列表"""
    return db.query(models.Image).filter(
        models.Image.user_id == user_id,
        models.Image.task_id == task_id
    ).all()

def get_images_by_user_and_task_and_company(
    db: Session,
    user_id: int,
    task_id: int,
    company: str
) -> List[models.Image]:
    """根据用户ID、任务ID和公司获取图片列表"""
    return db.query(models.Image).filter(
        models.Image.user_id == user_id,
        models.Image.task_id == task_id,
        models.Image.company == company
    ).all()

def update_image(db: Session, image_id: int, image_update: schemas.ImageUpdate) -> models.Image:
    """更新图片信息"""
    try:
        db_image = get_image(db, image_id)
        if not db_image:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        # 记录更新请求信息
        logger.info(f"更新图片 ID={image_id} 的信息")
        
        # 更新图片信息
        update_data = {k: v for k, v in image_update.dict(exclude_unset=True).items() 
                       if k != 'people_involved'}  # 先排除人员信息
        
        logger.info(f"更新图片字段: {list(update_data.keys())}")
        
        for key, value in update_data.items():
            setattr(db_image, key, value)
        
        # 更新时间戳
        db_image.updated_at = models.get_now_shanghai()
        
        # 先提交图片本身的更改
        db.commit()
        logger.info(f"已更新图片基本信息")
        
        # 如果有新的人员信息，则更新
        if image_update.people_involved is not None:
            people_count = len(image_update.people_involved)
            logger.info(f"处理图片关联的人员信息，共 {people_count} 人")
            
            try:
                # 先获取旧的关联人员
                old_persons = db.query(models.PersonInvolved).filter(
                    models.PersonInvolved.image_id == image_id
                ).all()
                
                old_count = len(old_persons)
                logger.info(f"图片原有 {old_count} 人，将被替换为 {people_count} 人")
                
                # 删除旧的关联人员
                if old_count > 0:
                    for old_person in old_persons:
                        logger.info(f"删除关联人员: ID={old_person.id}, 姓名={old_person.name}")
                        db.delete(old_person)
                    
                    db.commit()
                    logger.info(f"已删除所有旧的关联人员")
                
                # 添加新的关联人员
                if people_count > 0:
                    for i, person_data in enumerate(image_update.people_involved):
                        try:
                            logger.info(f"添加第 {i+1}/{people_count} 个人员: {person_data}")
                            
                            # 检查数据类型并处理
                            if isinstance(person_data, dict):
                                # 如果是字典而不是模型对象，创建模型对象
                                logger.info(f"将字典转换为PersonInvolved模型")
                                person = models.PersonInvolved(
                                    image_id=db_image.id,
                                    name=person_data.get('name', ''),
                                    id_number=person_data.get('id_number', ''),
                                    household_registration=person_data.get('household_registration', '')
                                )
                            else:
                                # 使用模型对象创建数据库记录
                                person = models.PersonInvolved(
                                    image_id=db_image.id,
                                    name=person_data.name,
                                    id_number=person_data.id_number,
                                    household_registration=person_data.household_registration
                                )
                            
                            db.add(person)
                            logger.info(f"已添加关联人员到数据库会话")
                        except Exception as e:
                            logger.error(f"添加第 {i+1} 个人员时出错: {str(e)}", exc_info=True)
                    
                    # 一次性提交所有人员
                    db.commit()
                    logger.info(f"已提交所有新的关联人员")
            except Exception as e:
                logger.error(f"更新人员信息过程中出错: {str(e)}", exc_info=True)
                db.rollback()
                # 不抛出异常，继续处理
        
        # 重新加载数据库对象，包括关联的人员
        db.refresh(db_image)
        
        logger.info(f"成功更新图片: ID={image_id}")
        return db_image
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"更新图片失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新图片失败: {str(e)}") 