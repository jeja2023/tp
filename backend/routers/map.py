from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
templates = Jinja2Templates(directory="frontend")

# 从环境变量获取高德地图API密钥
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "your_amap_api_key")

@router.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):
    try:
        return templates.TemplateResponse("map.html", {"request": request, "amap_api_key": AMAP_API_KEY})
    except Exception as e:
        print(f"Error rendering map page: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading map page") 