# Database models for the application

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base
import pytz

# 定义东八区时区
CN_TIMEZONE = pytz.timezone('Asia/Shanghai')

def get_now_shanghai():
    """获取当前上海时间"""
    return datetime.now(CN_TIMEZONE)

Base = declarative_base()

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    company = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_now_shanghai)
    
    tasks = relationship("Task", back_populates="owner")
    task_permissions = relationship("TaskPermission", back_populates="user", foreign_keys="TaskPermission.user_id")
    shared_permissions = relationship("TaskPermission", foreign_keys="TaskPermission.shared_by_id", overlaps="task_permissions")

class Task(Base):
    """Task model for organizing images"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_now_shanghai)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="tasks")
    images = relationship("Image", back_populates="task")
    permissions = relationship("TaskPermission", back_populates="task")

class TaskPermission(Base):
    """Task permission model for sharing tasks between users"""
    __tablename__ = "task_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    shared_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    permission_type = Column(String(20), default="view")  # 'view', 'edit', 'admin'
    can_upload = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=True)
    can_manage = Column(Boolean, default=False)
    
    task = relationship("Task", back_populates="permissions")
    user = relationship("User", back_populates="task_permissions", foreign_keys=[user_id])
    shared_by = relationship("User", foreign_keys=[shared_by_id], overlaps="shared_permissions")

class Image(Base):
    """Image model for storing image metadata"""
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    file_path = Column(String(255))
    time = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    transportation = Column(String(50), nullable=False)
    sequence_number = Column(Integer)
    created_at = Column(DateTime, default=get_now_shanghai)
    updated_at = Column(DateTime, default=get_now_shanghai, onupdate=get_now_shanghai)
    created_by = Column(String(50), nullable=True)
    
    task = relationship("Task", back_populates="images")
    people_involved = relationship("PersonInvolved", back_populates="image")

class PersonInvolved(Base):
    """Person involved model for tracking people in images"""
    __tablename__ = "people_involved"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"))
    name = Column(String(50))
    id_number = Column(String(18))
    household_registration = Column(String(255))
    
    image = relationship("Image", back_populates="people_involved") 