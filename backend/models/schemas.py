# Pydantic models for request/response validation

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, ForwardRef
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str
    phone: str
    company: str

class UserCreate(UserBase):
    password: str
    password_confirm: str
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v

class UserUpdate(BaseModel):
    phone: Optional[str] = None
    company: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_approved: Optional[bool] = None

class UserStatusUpdate(BaseModel):
    is_active: bool

class UserProfileUpdate(BaseModel):
    company: Optional[str] = None
    phone: Optional[str] = None

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str
    password_confirm: str
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Person involved schemas
class PersonInvolvedBase(BaseModel):
    name: str
    id_number: str
    household_registration: str

class PersonInvolvedCreate(PersonInvolvedBase):
    pass

class PersonInvolved(PersonInvolvedBase):
    id: int
    image_id: int

    class Config:
        from_attributes = True

# Image schemas
class ImageBase(BaseModel):
    file_path: str
    time: datetime
    location: str
    description: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    transportation: str
    sequence_number: Optional[int] = None
    created_by: Optional[str] = None

class ImageCreate(ImageBase):
    task_id: int
    people_involved: Optional[List[PersonInvolvedCreate]] = []

class ImageUpdate(BaseModel):
    file_path: Optional[str] = None
    time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    transportation: Optional[str] = None
    sequence_number: Optional[int] = None
    created_by: Optional[str] = None
    people_involved: Optional[List[PersonInvolvedCreate]] = None

class Image(ImageBase):
    id: int
    task_id: int
    created_at: datetime
    updated_at: datetime
    people_involved: List[PersonInvolved] = []

    class Config:
        from_attributes = True

# Task permission schemas
class TaskPermissionBase(BaseModel):
    permission_type: str  # 'view', 'edit', 'admin'
    can_upload: bool = True
    can_edit: bool = True
    can_manage: bool = False

class TaskPermissionCreate(TaskPermissionBase):
    username: str  # 用户名而不是用户ID
    
class TaskPermission(TaskPermissionBase):
    id: int
    user_id: Optional[int] = None  # 允许为空
    task_id: int

    class Config:
        from_attributes = True

# Task schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None

class TaskCreate(TaskBase):
    user_id: int

class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None

class Task(TaskBase):
    id: int
    created_at: datetime
    owner_id: int
    owner: Optional['User'] = None
    images: List[Image] = []
    permissions: List[TaskPermission] = []

    class Config:
        from_attributes = True

# 系统日志schemas
class SystemLogBase(BaseModel):
    level: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    request_id: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    status_code: Optional[int] = None
    process_time: Optional[float] = None
    timestamp: Optional[datetime] = None

class SystemLogCreate(SystemLogBase):
    pass

class SystemLog(SystemLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# 日志查询响应
class LogsResponse(BaseModel):
    logs: List[SystemLog]
    total: int
    total_pages: int
    page: int
    limit: int

# 单个日志响应
class SystemLogResponse(BaseModel):
    log: SystemLog

# 日志统计响应
class LogStatisticsResponse(BaseModel):
    total_logs: int
    logs_by_level: dict
    logs_by_source: dict
    logs_by_date: dict

# API请求日志响应模型
class ApiRequestLog(BaseModel):
    id: int
    timestamp: datetime
    level: str
    path: str
    method: str
    status_code: int
    process_time: float
    username: Optional[str] = None
    request_id: str
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True

# API请求日志列表响应模型
class ApiRequestLogsResponse(BaseModel):
    logs: List[ApiRequestLog]
    total: int
    total_pages: int
    page: int
    limit: int 