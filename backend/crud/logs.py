from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import pytz
from fastapi import HTTPException
from ..models import models, schemas
from ..utils.logger import setup_logger
from backend.config import settings
import csv
import os

# 创建日志记录器
logger = setup_logger("crud_logs")

def get_log(db: Session, log_id: int) -> Optional[models.SystemLog]:
    """获取单个日志"""
    return db.query(models.SystemLog).filter(models.SystemLog.id == log_id).first()

def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None,
    source: Optional[str] = None,
    user_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    request_path: Optional[str] = None,
    username: Optional[str] = None,
    search: Optional[str] = None
) -> List[models.SystemLog]:
    """获取日志列表"""
    query = db.query(models.SystemLog)
    
    if level:
        query = query.filter(models.SystemLog.level == level)
    if source:
        query = query.filter(models.SystemLog.source == source)
    if user_id:
        query = query.filter(models.SystemLog.user_id == user_id)
    if start_time:
        query = query.filter(models.SystemLog.timestamp >= start_time)
    if end_time:
        query = query.filter(models.SystemLog.timestamp <= end_time)
    if request_path:
        query = query.filter(models.SystemLog.request_path.ilike(f"%{request_path}%"))
    if username:
        query = query.filter(models.SystemLog.username.ilike(f"%{username}%"))
    if search:
        query = query.filter(models.SystemLog.message.ilike(f"%{search}%"))
    
    return query.order_by(models.SystemLog.timestamp.desc()).offset(skip).limit(limit).all()

def create_log(db: Session, log: schemas.SystemLogCreate) -> models.SystemLog:
    """创建新日志"""
    db_log = models.SystemLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def delete_log(db: Session, log_id: int) -> bool:
    """删除日志"""
    log = get_log(db, log_id)
    if log:
        db.delete(log)
        db.commit()
        return True
    return False

def get_logs_by_level(db: Session, level: str) -> List[models.SystemLog]:
    """获取指定级别的日志"""
    return db.query(models.SystemLog).filter(
        models.SystemLog.level == level
    ).all()

def log_activity(
    db: Session,
    level: str,
    message: str,
    source: Optional[str] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None,
    request_path: Optional[str] = None,
    request_method: Optional[str] = None,
    status_code: Optional[int] = None,
    process_time: Optional[float] = None
) -> models.SystemLog:
    """记录系统活动"""
    try:
        log_data = {
            "level": level,
            "message": message,
            "source": source,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "request_id": request_id,
            "request_path": request_path,
            "request_method": request_method,
            "status_code": status_code,
            "process_time": process_time
        }
        
        # 移除None值
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # 创建日志记录
        db_log = create_log(db, schemas.SystemLogCreate(**log_data))
        
        # 更新消息，添加日志ID
        db_log.message = f"{db_log.message} [ID:{db_log.id}]"
        db.commit()
        
        return db_log
    except Exception as e:
        logger.error(f"记录系统活动失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"记录系统活动失败: {str(e)}")

def get_log_statistics(
    db: Session,
    days: int = 7
) -> Dict[str, Any]:
    """获取日志统计信息"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # 计算开始日期
    start_date = datetime.now() - timedelta(days=days)
    
    # 基础查询
    base_query = db.query(models.SystemLog).filter(models.SystemLog.timestamp >= start_date)
    
    # 获取总日志数
    total_logs = base_query.count()
    
    # 按级别统计
    logs_by_level = dict(
        db.query(
            models.SystemLog.level,
            func.count(models.SystemLog.id)
        ).filter(
            models.SystemLog.timestamp >= start_date
        ).group_by(
            models.SystemLog.level
        ).all()
    )
    
    # 按来源统计
    logs_by_source = dict(
        db.query(
            models.SystemLog.source,
            func.count(models.SystemLog.id)
        ).filter(
            models.SystemLog.timestamp >= start_date
        ).group_by(
            models.SystemLog.source
        ).all()
    )
    
    # 按日期统计
    logs_by_date = dict(
        db.query(
            func.date(models.SystemLog.timestamp),
            func.count(models.SystemLog.id)
        ).filter(
            models.SystemLog.timestamp >= start_date
        ).group_by(
            func.date(models.SystemLog.timestamp)
        ).all()
    )
    
    # 转换日期为字符串
    logs_by_date = {
        date.strftime("%Y-%m-%d"): count
        for date, count in logs_by_date.items()
    }
    
    return {
        "total_logs": total_logs,
        "logs_by_level": logs_by_level,
        "logs_by_source": logs_by_source,
        "logs_by_date": logs_by_date
    }

def export_logs_to_csv(
    db: Session,
    level: Optional[str] = None,
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    search: Optional[str] = None
) -> str:
    """导出日志到CSV文件"""
    try:
        # 获取日志数据
        logs = get_logs(
            db=db,
            level=level,
            source=source,
            start_time=start_time,
            end_time=end_time,
            search=search
        )
        
        # 确保temp目录存在
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs_export_{timestamp}.csv"
        filepath = os.path.join(temp_dir, filename)
        
        # 写入CSV文件
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow([
                "时间", "级别", "来源", "用户名", "IP地址", "请求ID",
                "请求路径", "请求方法", "状态码", "处理时间(秒)", "消息"
            ])
            
            # 写入数据
            for log in logs:
                writer.writerow([
                    log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    log.level or "-",
                    log.source or "-",
                    log.username or "-",
                    log.ip_address or "-",
                    log.request_id or "-",
                    log.request_path or "-",
                    log.request_method or "-",
                    log.status_code or "-",
                    f"{log.process_time:.4f}" if log.process_time else "-",
                    log.message or "-"
                ])
        
        logger.info(f"日志已导出到文件: {filepath}")
        return filename
        
    except Exception as e:
        logger.error(f"导出日志失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出日志失败: {str(e)}")

def delete_old_logs(
    db: Session,
    days: int,
    **filters
) -> int:
    """删除指定天数前的日志"""
    from datetime import datetime, timedelta
    
    # 计算截止日期
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 构建查询
    query = db.query(models.SystemLog).filter(models.SystemLog.timestamp < cutoff_date)
    
    # 应用过滤条件
    for key, value in filters.items():
        if value is not None:
            if key == "exclude_source":
                query = query.filter(models.SystemLog.source != value)
            else:
                query = query.filter(getattr(models.SystemLog, key) == value)
    
    # 获取要删除的记录数
    count = query.count()
    
    # 执行删除
    query.delete(synchronize_session=False)
    db.commit()
    
    return count

def get_logs_count(
    db: Session,
    level: Optional[str] = None,
    source: Optional[str] = None,
    user_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    request_path: Optional[str] = None,
    username: Optional[str] = None,
    search: Optional[str] = None
) -> int:
    """获取日志总记录数"""
    query = db.query(models.SystemLog)
    
    if level:
        query = query.filter(models.SystemLog.level == level)
    if source:
        query = query.filter(models.SystemLog.source == source)
    if user_id:
        query = query.filter(models.SystemLog.user_id == user_id)
    if start_time:
        query = query.filter(models.SystemLog.timestamp >= start_time)
    if end_time:
        query = query.filter(models.SystemLog.timestamp <= end_time)
    if request_path:
        query = query.filter(models.SystemLog.request_path.ilike(f"%{request_path}%"))
    if username:
        query = query.filter(models.SystemLog.username.ilike(f"%{username}%"))
    if search:
        query = query.filter(models.SystemLog.message.ilike(f"%{search}%"))
    
    return query.count() 