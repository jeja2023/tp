from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..db import get_db
from ..utils.utils import verify_token
from starlette.middleware.base import BaseHTTPMiddleware
from ..models.models import User as models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 获取当前用户函数
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = verify_token(token, db)
    if user is None:
        raise credentials_exception
    return user

# 认证中间件
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 检查是否是API请求
        if request.url.path.startswith("/api/"):
            # 获取认证头
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    # 验证token并获取用户
                    user = await get_current_user(token, next(get_db()))
                    # 设置用户信息到request.state
                    request.state.user = user
                except HTTPException:
                    pass  # 认证失败，不设置用户信息
        
        response = await call_next(request)
        return response 