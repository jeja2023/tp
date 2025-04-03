from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from ..crud import logs as crud_logs
from ..db import SessionLocal
from ..utils.logger import setup_logger

logger = setup_logger("api_logging_middleware")

class APILoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        request_id = str(request.headers.get("X-Request-ID", "")) or "-"
        client_host = request.client.host if request.client else "-"
        
        # 获取用户信息（如果有）
        user_id = None
        username = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id
            username = request.state.user.username
        
        # 设置默认值
        user_id = user_id or "-"
        username = username or "-"
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 构建日志消息
            log_message = f"API请求: {request.method} {request.url.path}"
            
            # 添加查询参数
            if request.query_params:
                query_params = dict(request.query_params)
                log_message += f"\n查询参数: {query_params}"
            
            # 添加请求体（如果有）
            try:
                body = await request.body()
                if body:
                    log_message += f"\n请求体: {body.decode()}"
            except:
                pass
            
            # 记录API请求日志
            try:
                db = SessionLocal()
                crud_logs.log_activity(
                    db=db,
                    level="INFO" if response.status_code < 400 else "WARNING",
                    message=log_message,
                    source="API",
                    user_id=user_id if user_id != "-" else None,
                    username=username if username != "-" else None,
                    ip_address=client_host if client_host != "-" else None,
                    request_id=request_id if request_id != "-" else None,
                    request_path=request.url.path,
                    request_method=request.method,
                    status_code=response.status_code,
                    process_time=process_time
                )
            except Exception as e:
                logger.error(f"记录API请求日志失败: {str(e)}", exc_info=True)
            finally:
                db.close()
            
            return response
            
        except Exception as e:
            # 构建错误日志消息
            error_message = f"API请求异常: {str(e)}"
            
            # 添加请求信息
            error_message += f"\n请求路径: {request.url.path}"
            error_message += f"\n请求方法: {request.method}"
            
            # 添加查询参数
            if request.query_params:
                query_params = dict(request.query_params)
                error_message += f"\n查询参数: {query_params}"
            
            # 记录错误日志
            try:
                db = SessionLocal()
                crud_logs.log_activity(
                    db=db,
                    level="ERROR",
                    message=error_message,
                    source="API",
                    user_id=user_id if user_id != "-" else None,
                    username=username if username != "-" else None,
                    ip_address=client_host if client_host != "-" else None,
                    request_id=request_id if request_id != "-" else None,
                    request_path=request.url.path,
                    request_method=request.method,
                    status_code=500,
                    process_time=time.time() - start_time
                )
            except Exception as log_error:
                logger.error(f"记录API错误日志失败: {str(log_error)}", exc_info=True)
            finally:
                db.close()
            
            raise 