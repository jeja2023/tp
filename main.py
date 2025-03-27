from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
import os
import uvicorn
import sys
from backend.utils.logger import setup_logger
from fastapi.templating import Jinja2Templates

# 使用新的日志配置
logger = setup_logger("app")

try:
    # 导入数据库模型
    from backend.models.models import Base
    from backend.db.database import engine, IS_PRODUCTION

    # 导入路由
    from backend.routers.base import router as base_router
    from backend.routers.users import router as users_router, oauth2_router
    from backend.routers.tasks import router as tasks_router
    from backend.routers.images import router as images_router
    from backend.routers.trajectory import router as trajectory_router
    from backend.routers.map import router as map_router

    # 创建数据库表
    Base.metadata.create_all(bind=engine)
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

# 创建上传和输出目录
for directory in ["uploads", "outputs"]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")

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

# 从环境变量获取高德地图API密钥
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "your_amap_api_key")

templates = Jinja2Templates(directory="frontend")

# 主程序入口
if __name__ == "__main__":
    # 生产环境设置
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "8000"))
    reload_flag = not IS_PRODUCTION  # 生产环境不使用热重载
    
    logger.info(f"应用启动: 环境={('生产' if IS_PRODUCTION else '开发')}, 主机={host}, 端口={port}")
    uvicorn.run("main:app", host=host, port=port, reload=reload_flag)

