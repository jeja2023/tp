from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from config import settings
import os
from fastapi import HTTPException

router = APIRouter(tags=["base"])
templates = Jinja2Templates(directory="frontend")

# 配置前端首页
@router.get("/")
async def read_index(request: Request):
    return RedirectResponse(url="/login")

# 配置登录页面
@router.get("/login")
async def read_login(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "amap_api_key": settings.AMAP_API_KEY
    })

# 配置主页
@router.get("/index")
async def read_home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "amap_api_key": settings.AMAP_API_KEY
    })

# 配置任务管理页面
@router.get("/task")
async def read_task(request: Request):
    return templates.TemplateResponse("task.html", {
        "request": request,
        "amap_api_key": settings.AMAP_API_KEY
    })

# 配置任务详情页面
@router.get("/upload")
async def read_upload(request: Request):
    # 添加日志，检查传递的参数
    print(f"提供API密钥: {settings.AMAP_API_KEY}")
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "amap_api_key": settings.AMAP_API_KEY
    })

# 配置任务图片列表页面
@router.get("/image")
async def read_image(request: Request):
    return templates.TemplateResponse("image.html", {
        "request": request,
        "amap_api_key": settings.AMAP_API_KEY
    })

# 配置管理员页面
@router.get("/admin")
async def read_admin(request: Request):
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "amap_api_key": settings.AMAP_API_KEY
    })

# 添加一个测试路由
@router.get("/test")
async def test():
    return {"message": "Test successful! System working normally."}

# 处理图片访问
@router.get("/api/uploads/{task_id}/{filename}")
async def get_image(task_id: str, filename: str):
    file_path = os.path.join("uploads", task_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(file_path) 