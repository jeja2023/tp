from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..db import get_db
from ..utils.utils import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 获取当前用户函数
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = verify_token(token, credentials_exception, db)
    if user is None:
        raise credentials_exception
    return user 