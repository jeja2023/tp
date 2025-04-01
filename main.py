#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
import os
import uvicorn
import sys
from backend.utils.logger import setup_logger
from fastapi.templating import Jinja2Templates
from backend.utils.key_manager import KeyManager
from config import settings

# 使用新的日志配置
logger = setup_logger("app")

try:
    # 导入数据库模型
    from backend.models.models import Base
    from backend.db.database import engine, IS_PRODUCTION
    from backend.db.initialize_db import initialize_base_data

    # 导入路由
    from backend.routers.base import router as base_router
    from backend.routers.users import router as users_router, oauth2_router
    from backend.routers.tasks import router as tasks_router
    from backend.routers.images import router as images_router
    from backend.routers.trajectory import router as trajectory_router
    from backend.routers.map import router as map_router

    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    # 初始化基础数据（包括管理员账户）
    initialize_base_data()
except Exception as e:
    logger.error(f"启动出错: {str(e)}", exc_info=True)
    sys.exit(1)

# 创建FastAPI应用
app = FastAPI(
    title="在线图片管理系统", 
    description="一个用于管理图片、GPS轨迹和报告生成的系统",
    version="1.0.0",
    docs_url=None if IS_PRODUCTION else "/docs",  # 生产环境不显示API文档
    redoc_url=None if IS_PRODUCTION else "/redoc"
)

# 配置CORS
origins = ["*"] if not IS_PRODUCTION else ["https://your-domain.com"]  # 生产环境应限制允许的源
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(base_router)  # 移除prefix参数
app.include_router(users_router, prefix="/api")
app.include_router(oauth2_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(trajectory_router, prefix="/api/trajectory")
app.include_router(map_router)  # 添加地图路由

# 配置静态文件路由
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

templates = Jinja2Templates(directory="frontend")

# 初始化密钥管理器（在config导入完成后）
@app.on_event("startup")
async def startup_event():
    try:
        # 初始化密钥管理器
        key_manager = KeyManager()
        
        # 记录密钥状态信息（不包含密钥本身）
        key_info = key_manager.get_key_info()
        logger.info(f"密钥状态: 上次轮换={key_info['last_rotation']}, 下次轮换={key_info['next_rotation']}, 剩余天数={key_info['days_until_rotation']}")
        
        # 检查并更新密钥
        new_key = key_manager.rotate_key()
        if new_key:
            logger.info(f"密钥已更新，系统安全性已增强")
            
            # 确保utils.py中的SECRET_KEY被更新
            from backend.utils import utils
            # 强制刷新utils模块中的SECRET_KEY
            utils.SECRET_KEY = key_manager.get_current_key()
            logger.info(f"应用接口安全密钥已更新")
        else:
            logger.info("密钥验证完成，当前密钥有效")
            
            # 确保utils.py中的SECRET_KEY是最新的
            from backend.utils import utils
            current_key = key_manager.get_current_key()
            if utils.SECRET_KEY != current_key:
                utils.SECRET_KEY = current_key
                logger.warning("检测到utils模块中的密钥不一致，已更新为最新密钥")
        
        # 记录安全审计信息
        if IS_PRODUCTION:
            logger.info("生产环境安全审计: JWT密钥已验证，密钥轮换机制已启用")
        
        # 记录离线地图配置信息
        logger.info(f"使用离线地图: 路径={settings.MAP_TILE_PATH}, 默认缩放={settings.MAP_DEFAULT_ZOOM}")
    except Exception as e:
        logger.error(f"初始化密钥管理器出错: {str(e)}", exc_info=True)
        # 不退出程序，允许继续运行，但记录错误

# 主程序入口
if __name__ == "__main__":
    # 生产环境设置
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "8000"))
    reload_flag = not IS_PRODUCTION  # 生产环境不使用热重载
    
    logger.info(f"应用启动: 环境={('生产' if IS_PRODUCTION else '开发')}, 主机={host}, 端口={port}")
    uvicorn.run("main:app", host=host, port=port, reload=reload_flag)

