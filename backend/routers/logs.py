from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, Form
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..models import models, schemas
from ..db import get_db
from ..api import get_current_user, oauth2_scheme
from ..utils.logger import setup_logger
from ..utils.utils import SECRET_KEY as JWT_SECRET_KEY, ALGORITHM
from backend.config import settings
from jose import JWTError, jwt
from ..models.schemas import SystemLog, LogsResponse, SystemLogResponse, LogStatisticsResponse
from ..models.models import User
from ..crud import logs as crud_logs
import os

# 创建日志记录器
logger = setup_logger("logs_router")

router = APIRouter(
    prefix="",
    tags=["logs"]
)

# 日志设置模型
class LogSettings(BaseModel):
    enable_file_logging: bool
    log_level: Optional[str] = "INFO"
    retention_days: Optional[int] = 30

# 获取日志设置
@router.get("/logs/settings", response_model=LogSettings)
async def get_log_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前日志设置，只有管理员可以访问"""
    try:
        # 检查是否是管理员
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以查看日志设置")
        
        # 记录操作
        crud_logs.log_activity(
            db=db,
            level="INFO",
            source="ADMIN",
            message=f"管理员 {current_user.username} 查看了日志设置",
            username=current_user.username
        )
        
        # 返回当前设置
        return LogSettings(
            enable_file_logging=settings.ENABLE_FILE_LOGGING,
            log_level=settings.LOG_LEVEL,
            retention_days=settings.LOG_RETENTION_DAYS
        )
    except Exception as e:
        logger.error(f"获取日志设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取日志设置失败: {str(e)}")

# 更新日志设置
@router.put("/logs/settings", response_model=LogSettings)
async def update_log_settings(
    log_settings: LogSettings,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新日志设置，只有管理员可以修改"""
    try:
        # 检查是否是管理员
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改日志设置")
        
        # 验证日志级别
        if log_settings.log_level and log_settings.log_level.upper() not in ['INFO', 'WARNING', 'ERROR', 'DEBUG']:
            raise HTTPException(status_code=400, detail="无效的日志级别")
        
        # 验证保留天数
        if log_settings.retention_days and (log_settings.retention_days < 1 or log_settings.retention_days > 365):
            raise HTTPException(status_code=400, detail="日志保留天数必须在1-365天之间")
        
        # 更新设置
        settings.ENABLE_FILE_LOGGING = log_settings.enable_file_logging
        if log_settings.log_level:
            settings.LOG_LEVEL = log_settings.log_level.upper()
        if log_settings.retention_days:
            settings.LOG_RETENTION_DAYS = log_settings.retention_days
        
        # 记录操作
        action = "启用" if log_settings.enable_file_logging else "禁用"
        message = f"管理员 {current_user.username} 更新了日志设置：{action}文件日志记录，日志级别={settings.LOG_LEVEL}，保留天数={settings.LOG_RETENTION_DAYS}天"
        
        crud_logs.log_activity(
            db=db,
            level="INFO",
            source="ADMIN",
            message=message,
            user_id=current_user.id,
            username=current_user.username
        )
        
        logger.info(message)
        
        return log_settings
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"更新日志设置失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新日志设置失败: {str(e)}")

# 获取系统日志
@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    level: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统日志"""
    try:
        # 检查用户权限
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以访问日志")
        
        # 转换日期字符串为datetime对象
        start_datetime = datetime.fromisoformat(start_date) if start_date else None
        end_datetime = datetime.fromisoformat(end_date) if end_date else None
        
        # 计算skip值
        skip = (page - 1) * limit
        
        # 获取日志
        logs = crud_logs.get_logs(
            db=db,
            skip=skip,
            limit=limit,
            level=level,
            search=search,
            start_time=start_datetime,
            end_time=end_datetime
        )
        
        # 获取总记录数
        total = crud_logs.get_logs_count(
            db=db,
            level=level,
            search=search,
            start_time=start_datetime,
            end_time=end_datetime
        )
        
        # 计算总页数
        total_pages = (total + limit - 1) // limit
        
        return LogsResponse(
            logs=logs,
            total=total,
            total_pages=total_pages,
            page=page,
            limit=limit
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

# 导出系统日志 (GET方式)
@router.get("/logs/export")
async def export_logs(
    level: Optional[str] = Query(None, description="日志级别"),
    source: Optional[str] = Query(None, description="日志来源"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出日志到CSV文件"""
    try:
        # 检查是否是管理员
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以导出日志")
        
        # 记录导出操作
        crud_logs.log_activity(
            db=db,
            level="INFO",
            source="ADMIN",
            message=f"管理员 {current_user.username} 导出日志",
            username=current_user.username
        )
        
        # 导出日志
        filename = crud_logs.export_logs_to_csv(
            db=db,
            level=level,
            source=source,
            start_time=start_time,
            end_time=end_time,
            search=search
        )
        
        # 构建文件路径
        filepath = os.path.join("backend", "temp", filename)
        
        # 返回文件
        return FileResponse(
            filepath,
            filename=filename,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"导出日志失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

# 获取日志统计信息
@router.get("/logs/statistics", response_model=LogStatisticsResponse)
async def get_log_statistics(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取日志统计信息"""
    try:
        # 检查用户权限
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以访问日志统计")
        
        # 获取统计信息
        statistics = crud_logs.get_log_statistics(db=db, days=days)
        
        # 记录操作
        crud_logs.log_activity(
            db=db,
            level="INFO",
            source="ADMIN",
            message=f"管理员 {current_user.username} 查看了日志统计信息",
            user_id=current_user.id,
            username=current_user.username
        )
        
        return LogStatisticsResponse(**statistics)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取日志统计信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取日志统计信息失败: {str(e)}")

# 删除旧日志
@router.delete("/logs/cleanup")
async def cleanup_old_logs(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除指定天数前的日志"""
    try:
        # 检查用户权限
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以清理日志")
        
        # 删除旧日志
        deleted_count = crud_logs.delete_old_logs(db=db, days=days)
        
        # 记录操作
        crud_logs.log_activity(
            db=db,
            level="INFO",
            source="ADMIN",
            message=f"管理员 {current_user.username} 清理了{days}天前的日志，共删除{deleted_count}条记录",
            user_id=current_user.id,
            username=current_user.username
        )
        
        return {"message": f"成功删除{deleted_count}条旧日志记录"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"清理旧日志失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理旧日志失败: {str(e)}")

# 通过POST方式导出日志（解决前端授权问题）
@router.post("/logs/export", status_code=200)
async def export_logs_post(
    request: Request,
    format: str = Form("csv", description="导出格式，目前仅支持CSV"),
    log_type: str = Form("system", description="日志类型，system或api"),
    level: Optional[str] = Form(None, description="日志级别"),
    search: Optional[str] = Form(None, description="搜索关键字"),
    token: str = Form(..., description="认证令牌"),
    db: Session = Depends(get_db)
):
    """通过POST表单提交方式导出日志，解决前端授权问题"""
    # 验证token
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="无效的认证信息")
            
        # 获取用户
        current_user = crud_logs.get_user_by_username(db, username)
        if not current_user:
            raise HTTPException(status_code=401, detail="用户不存在")
        
        # 检查是否是管理员
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以导出系统日志")
    except JWTError:
        raise HTTPException(status_code=401, detail="认证已过期")
    
    # 目前仅支持CSV格式
    if format.lower() != "csv":
        raise HTTPException(status_code=400, detail="不支持的导出格式，目前仅支持CSV")
    
    # 根据日志类型选择导出函数
    if log_type == "api":
        # 导出API请求日志
        filters = {"source": "API"}
        if level:
            filters["level"] = level
        if search:
            filters["search"] = search
        
        csv_data = crud_logs.export_logs_to_csv(db, **filters)
        filename = f"api_request_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        log_description = "API请求日志"
    else:
        # 导出普通系统日志
        csv_data = crud_logs.export_logs_to_csv(db, level=level, search=search)
        filename = f"system_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        log_description = "系统日志"
    
    # 记录导出日志操作
    crud_logs.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} 通过POST方式导出{log_description}，过滤条件：level={level}, search={search}",
        user_id=current_user.id,
        username=current_user.username
    )
    
    # 返回CSV文件
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8-sig"
        }
    )

# 添加系统日志
@router.post("/logs/add", response_model=schemas.SystemLog)
async def add_log(
    log: schemas.SystemLogCreate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以添加系统日志")
    
    # 如果没有提供用户信息，使用当前用户
    if not log.user_id:
        log.user_id = current_user.id
    if not log.username:
        log.username = current_user.username
    
    # 获取客户端IP
    if not log.ip_address:
        log.ip_address = request.client.host
    
    # 创建日志
    db_log = crud_logs.create_log(db, log)
    
    return db_log

# 通过POST方式清理日志
@router.post("/logs/cleanup_post")
async def cleanup_logs_post(
    request: Request,
    cleanup_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过POST方式清理旧日志，接收JSON格式的参数"""
    try:
        # 从请求数据中提取参数
        days = cleanup_data.get("days", 30)
        log_type = cleanup_data.get("log_type", "system")
        
        # 参数验证
        if not isinstance(days, (int, float)):
            raise HTTPException(status_code=400, detail="days参数必须是数字")
        
        days = int(days)
        if days < 1:
            raise HTTPException(status_code=400, detail="days参数必须大于等于1")
        
        if days > 365:
            raise HTTPException(status_code=400, detail="days参数不能大于365")
        
        if log_type not in ["system", "api"]:
            raise HTTPException(status_code=400, detail="log_type参数必须是'system'或'api'")
        
        # 检查是否是管理员
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以清理系统日志")
        
        # 记录开始清理的日志
        logger.info(f"开始清理{days}天前的{log_type}日志，操作者：{current_user.username}")
        
        # 根据日志类型清理
        if log_type == "api":
            # 清理API请求日志
            filters = {"source": "API"}
            deleted_count = crud_logs.delete_old_logs(db, days=days, **filters)
            log_description = "API请求日志"
        else:
            # 清理普通系统日志，排除API日志
            filters = {"exclude_source": "API"}
            deleted_count = crud_logs.delete_old_logs(db, days=days, **filters)
            log_description = "系统日志"
        
        # 记录清理操作
        message = f"管理员 {current_user.username} 清理了 {deleted_count} 条 {days} 天前的{log_description}记录"
        crud_logs.log_activity(
            db=db,
            level="INFO",
            source="ADMIN",
            message=message,
            user_id=current_user.id,
            username=current_user.username
        )
        
        logger.info(message)
        
        return {
            "status": "success",
            "deleted": deleted_count,
            "message": f"成功删除 {deleted_count} 条 {days} 天前的{log_description}记录"
        }
        
    except HTTPException as e:
        # 记录HTTP异常
        logger.warning(f"日志清理失败：{str(e.detail)}，操作者：{current_user.username}")
        raise
        
    except Exception as e:
        # 记录其他异常
        error_message = f"日志清理过程中发生错误：{str(e)}"
        logger.error(error_message, exc_info=True)
        
        # 记录到数据库
        crud_logs.log_activity(
            db=db,
            level="ERROR",
            source="ADMIN",
            message=f"清理日志失败：{str(e)}",
            user_id=current_user.id,
            username=current_user.username
        )
        
        raise HTTPException(status_code=500, detail=error_message)

# 获取API请求日志
@router.get("/logs/requests", response_model=schemas.ApiRequestLogsResponse)
async def get_request_logs(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(50, ge=10, le=100, description="每页记录数"),
    level: Optional[str] = Query(None, description="日志级别 (INFO, WARNING, ERROR)"),
    path: Optional[str] = Query(None, description="请求路径"),
    method: Optional[str] = Query(None, description="请求方法"),
    status_code: Optional[int] = Query(None, ge=100, le=599, description="响应状态码"),
    username: Optional[str] = Query(None, description="用户名"),
    request_id: Optional[str] = Query(None, description="请求ID"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取API请求日志，支持分页和过滤"""
    try:
        # 检查是否是管理员
        if not current_user.is_admin:
            logger.warning(f"非管理员用户 {current_user.username} 尝试访问API请求日志")
            raise HTTPException(status_code=403, detail="只有管理员可以查看API请求日志")
        
        # 构建过滤条件
        filters = {
            "source": "API",  # 只获取API来源的日志
            "level": level,
            "request_path": path,
            "request_method": method,
            "status_code": status_code,
            "username": username,
            "request_id": request_id
        }
        
        # 移除None值的过滤条件
        filters = {k: v for k, v in filters.items() if v is not None}
        
        logger.debug(f"获取API请求日志，过滤条件：{filters}")
        
        try:
            # 获取总记录数
            total = crud_logs.get_logs_count(db, **filters)
    
            # 获取日志数据
            logs = crud_logs.get_logs(
                db=db,
                skip=(page - 1) * limit,
                limit=limit,
                **filters
            )
            
            # 计算总页数
            total_pages = (total + limit - 1) // limit
            
            # 转换日志数据为API请求日志格式
            api_logs = []
            for log in logs:
                try:
                    api_log = schemas.ApiRequestLog(
                        id=log.id,
                        timestamp=log.timestamp,
                        level=log.level,
                        path=log.request_path or "",
                        method=log.request_method or "",
                        status_code=log.status_code or 0,
                        process_time=log.process_time or 0.0,
                        username=log.username,
                        request_id=log.request_id or "",
                        ip_address=log.ip_address or ""
                    )
                    api_logs.append(api_log)
                except Exception as e:
                    logger.error(f"转换日志数据失败，日志ID: {log.id}, 错误: {str(e)}", exc_info=True)
                    continue
    
            # 记录查询日志操作
            try:
                crud_logs.log_activity(
                    db=db,
                    level="INFO",
                    source="ADMIN",
                    message=f"管理员 {current_user.username} 查询API请求日志，过滤条件：{filters}",
                    user_id=current_user.id,
                    username=current_user.username
                )
            except Exception as e:
                logger.error(f"记录日志查询操作失败: {str(e)}", exc_info=True)
            
            logger.debug(f"成功获取 {len(api_logs)} 条API请求日志")
            
            return schemas.ApiRequestLogsResponse(
                logs=api_logs,
                total=total,
                total_pages=total_pages,
                page=page,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"从数据库获取日志数据失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"从数据库获取日志数据失败: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取API请求日志失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

# 获取请求日志统计信息
@router.get("/logs/stats")
async def get_log_stats(
    days: int = Query(7, ge=1, le=90, description="统计过去几天的日志"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取API请求日志的统计信息，包括：
    - 按日分组的请求数量
    - 最常访问的路径
    - 请求方法分布
    - 状态码分布
    - 平均处理时间
    """
    # 检查是否是管理员
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看日志统计信息")
    
    # 获取统计数据
    stats = crud_logs.get_log_statistics(db, days=days)
    
    # 记录操作
    crud_logs.log_activity(
        db=db,
        level="INFO",
        source="ADMIN",
        message=f"管理员 {current_user.username} 查看了过去 {days} 天的日志统计信息",
        user_id=current_user.id,
        username=current_user.username
    )
    
    return stats 