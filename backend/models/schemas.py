# Pydantic models for request/response validation

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, ForwardRef
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None

class UserCreate(UserBase):
    password: str
    password_confirm: str

class UserStatusUpdate(BaseModel):
    is_active: bool

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
    user_id: int
    task_id: int

    class Config:
        from_attributes = True

# Task schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None

class TaskCreate(TaskBase):
    pass

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