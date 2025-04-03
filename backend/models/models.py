#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    company = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_now_shanghai)
    updated_at = Column(DateTime(timezone=True), default=get_now_shanghai, onupdate=get_now_shanghai)
    
    # 关联
    tasks = relationship("Task", back_populates="owner")
    images = relationship("Image", back_populates="user")
    logs = relationship("SystemLog", back_populates="user")
    task_permissions = relationship("TaskPermission", foreign_keys="[TaskPermission.user_id]")
    shared_tasks = relationship("TaskPermission", foreign_keys="[TaskPermission.shared_by_id]")

class Task(Base):
    """Task model for organizing images"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_now_shanghai)
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
    shared_by = relationship("User", back_populates="shared_tasks", foreign_keys=[shared_by_id])

class Image(Base):
    """Image model for storing image metadata"""
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    file_path = Column(String(255))
    time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    transportation = Column(String(50), nullable=False)
    sequence_number = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=get_now_shanghai)
    updated_at = Column(DateTime(timezone=True), default=get_now_shanghai, onupdate=get_now_shanghai)
    created_by = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    task = relationship("Task", back_populates="images")
    user = relationship("User", back_populates="images")
    people_involved = relationship("PersonInvolved", back_populates="image")

class PersonInvolved(Base):
    """Person involved model for tracking people in images"""
    __tablename__ = "people_involved"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"))
    name = Column(String(50))
    id_number = Column(String(18))
    household_registration = Column(String(255))
    
    image = relationship("Image", back_populates="people_involved")

class SystemLog(Base):
    """System log model for tracking system activities"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=get_now_shanghai)  # 使用东八区时间
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, etc.
    message = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)  # 来源模块或功能
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)  # 用户名
    ip_address = Column(String(50), nullable=True)
    request_id = Column(String(50), nullable=True)  # 请求ID
    request_path = Column(String(255), nullable=True)  # 请求路径
    request_method = Column(String(10), nullable=True)  # 请求方法
    status_code = Column(Integer, nullable=True)  # 响应状态码
    process_time = Column(Float, nullable=True)  # 处理时间（秒）
    
    user = relationship("User", back_populates="logs") 