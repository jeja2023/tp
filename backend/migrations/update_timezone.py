#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pytz
from models.models import Base, get_now_shanghai
from config.settings import settings

def update_timezone():
    """更新数据库中的时间为东八区时间"""
    print("开始更新数据库时间为东八区...")
    
    # 创建数据库连接
    engine = create_engine(settings.DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 更新 Task 表
        print("更新 Task 表...")
        db.execute(text("""
            UPDATE tasks 
            SET created_at = DATE_ADD(created_at, INTERVAL 8 HOUR)
            WHERE created_at IS NOT NULL;
        """))
        
        # 更新 Image 表
        print("更新 Image 表...")
        db.execute(text("""
            UPDATE images 
            SET created_at = DATE_ADD(created_at, INTERVAL 8 HOUR),
                updated_at = DATE_ADD(updated_at, INTERVAL 8 HOUR)
            WHERE created_at IS NOT NULL;
        """))
        
        # 更新 User 表
        print("更新 User 表...")
        db.execute(text("""
            UPDATE users 
            SET created_at = DATE_ADD(created_at, INTERVAL 8 HOUR),
                updated_at = DATE_ADD(updated_at, INTERVAL 8 HOUR)
            WHERE created_at IS NOT NULL;
        """))
        
        # 更新 SystemLog 表
        print("更新 SystemLog 表...")
        db.execute(text("""
            UPDATE system_logs 
            SET timestamp = DATE_ADD(timestamp, INTERVAL 8 HOUR)
            WHERE timestamp IS NOT NULL;
        """))
        
        # 提交更改
        db.commit()
        print("数据库时间更新完成！")
        
    except Exception as e:
        print(f"更新过程中出错: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    update_timezone() 